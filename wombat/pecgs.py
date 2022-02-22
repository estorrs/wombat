import os
import re
import uuid
import shutil
import yaml
from pathlib import Path

import wombat.bsub as bsub


COMPUTE1_TN_WXS_FQ_T_RNA_FQ_DEFAULTS = os.path.join(
    Path(__file__).parent.absolute(), 'templates', 'compute1.defaults.pecgs_TN_wxs_fq_T_rna_fq.yaml')


def get_sequencing_info(si):
    return {
        'wxs_tumor_flowcell': si['tumor']['flowcell'],
        'wxs_tumor_lane': si['tumor']['lane'],
        'wxs_tumor_index_sequencer': si['tumor']['index_sequencer'],
        'wxs_tumor_library_preparation': si['tumor']['library_preparation'],
        'wxs_tumor_platform': si['tumor']['platform'],
        'wxs_normal_flowcell': si['normal']['flowcell'],
        'wxs_normal_lane': si['normal']['lane'],
        'wxs_normal_index_sequencer': si['normal']['index_sequencer'],
        'wxs_normal_library_preparation': si['normal']['library_preparation'],
        'wxs_normal_platform': si['normal']['platform'],
    }


def populate_defaults_TN_wxs_fq_T_rna_fq(
        sample, tumor_wxs_fq_1, tumor_wxs_fq_2,
        normal_wxs_fq_1, normal_wxs_fq_2,
        tumor_rna_fq_1, tumor_rna_fq_2, cpu=40):
    d = {
        'sample': sample,
        'cpu': cpu,
        'tumor_wxs_fq_1': {
            'class': 'File',
            'path': tumor_wxs_fq_1
        },
        'tumor_wxs_fq_2': {
            'class': 'File',
            'path': tumor_wxs_fq_2
        },
        'normal_wxs_fq_1': {
            'class': 'File',
            'path': normal_wxs_fq_1
        },
        'normal_wxs_fq_2': {
            'class': 'File',
            'path': normal_wxs_fq_2
        },
        'tumor_rna_fq_1': {
            'class': 'File',
            'path': tumor_rna_fq_1
        },
        'tumor_rna_fq_2': {
            'class': 'File',
            'path': tumor_rna_fq_2
        }

    }

    d.update(yaml.safe_load(open(COMPUTE1_TN_WXS_FQ_T_RNA_FQ_DEFAULTS)))

    return d


def generate_input_TN_wxs_fq_T_rna_fq(sample, m, sequencing_info=None, cpu=40):
    d = populate_defaults_TN_wxs_fq_T_rna_fq(
        sample,
        m['wxs_tumor_R1'], m['wxs_tumor_R2'],
        m['wxs_normal_R1'], m['wxs_normal_R2'],
        m['rna-seq_tumor_R1'], m['rna-seq_tumor_R2'],
        cpu=cpu)

    if sequencing_info is not None:
        d.update(get_sequencing_info(sequencing_info))

    return d


def generate_sequencing_info_map(sequencing_info):
    sq = sequencing_info[[True if x.lower() == 'wxs' else False
                         for x in sequencing_info['experimental_strategy']]]
    run_ids = sorted(set(sq.index))
    m = {}
    for run_id in run_ids:
        m[run_id] = {'tumor': {}, 'normal': {}}

        f = sq[sq.index == run_id]
        for i, row in f.iterrows():
            m[run_id][row['sample_type']]['flowcell'] = row['flowcell']
            m[run_id][row['sample_type']]['lane'] = row['lane']
            m[run_id][row['sample_type']]['index_sequencer'] = row['index_sequencer']
            m[run_id][row['sample_type']]['library_preparation'] = row['library_preparation']
            m[run_id][row['sample_type']]['platform'] = row['platform']
    return m


def from_run_list_TN_wxs_fq_T_rna_fq(
        run_list, run_dir, tool_root, sequencing_info=None,
        job_group=None, n_concurrent=None, proxy_run_dir=None,
        input_kwargs=None, additional_volumes=None):
    log_dir = os.path.join(run_dir, 'logs')
    input_dir = os.path.join(run_dir, 'inputs')
    workflow_dir = os.path.join(run_dir, 'runs')

    sequencing_info_map = generate_sequencing_info_map(sequencing_info)
    inputs_fps, dconfigs, run_names = [], [], []
    for sample, d in run_list.items():
        input = generate_input_TN_wxs_fq_T_rna_fq(
            sample, d, sequencing_info_map.get(sample))
        if input_kwargs is not None:
            input.update(input_kwargs)
        input_fp = os.path.join(input_dir, f'{sample}.input.yaml')

        if proxy_run_dir is None:
            yaml.safe_dump(input, open(input_fp, 'w'))
        else:
            proxy_input_dir = os.path.join(proxy_run_dir, 'inputs')
            Path(proxy_input_dir).mkdir(parents=True, exist_ok=True)
            yaml.safe_dump(input, open(os.path.join(proxy_input_dir,
                f'{sample}.input.yaml'), 'w'))

        inputs_fps.append(input_fp)

        workflow_root = os.path.join(workflow_dir, sample)
        template_fp = os.path.join(
            input_dir, f'{sample}.cromwell-config-db.compute1.dat')
        if proxy_run_dir is None:
            bsub.save_compute1_cromwell_template(workflow_root, template_fp)
        else:
            proxy_template_fp = os.path.join(
                proxy_input_dir, f'{sample}.cromwell-config-db.compute1.dat')
            bsub.save_compute1_cromwell_template(
                workflow_root, proxy_template_fp)

        dconfigs.append(template_fp)

        run_names.append(sample)
    server_fp = os.path.join(input_dir, 'server-cromwell-config.compute1.dat')

    if proxy_run_dir is None:
        shutil.copy(bsub.DEFAULT_CROMWELL_SERVER_TEMPLATE, server_fp)
    else:
        proxy_server_fp = os.path.join(proxy_input_dir, 'server-cromwell-config.compute1.dat')
        shutil.copy(bsub.DEFAULT_CROMWELL_SERVER_TEMPLATE, proxy_server_fp)

    tool_root = '/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline'
    cwl_fp = os.path.join(
        tool_root, 'cwl', 'pecgs_workflows', 'pecgs_TN_wxs_fq_T_rna_fq.cwl')
    volumes = [run_dir, tool_root, '/storage1/fs1/dinglab',
               '/storage1/fs1/m.wyczalkowski/Active', '/scratch1/fs1/dinglab']
    if additional_volumes is not None:
        volumes += additional_volumes

    args = bsub.DEFAULT_ARGS
    if job_group is not None:
        args['group_name'] = job_group
    else:
        args['group_name'] = None
    if n_concurrent is not None:
        args['n_concurrent'] = n_concurrent
    else:
        args['n_concurrent'] = 25

    system_run_dir = run_dir if proxy_run_dir is None else proxy_run_dir
    start_commands, cromwell_server_command, run_commands = bsub.batch_cromwell_commands(
        dconfigs, server_fp, cwl_fp, inputs_fps, run_names, log_dir, workflow_dir, args, volumes)
    filepath = os.path.join(system_run_dir, '1.start_server.sh')
    bsub.write_command_file(start_commands, filepath)
    filepath = os.path.join(system_run_dir, '2.start_cromwell.sh')
    bsub.write_command_file([cromwell_server_command], filepath)
    filepath = os.path.join(system_run_dir, '3.run_jobs.sh')
    bsub.write_command_file(run_commands, filepath)

    return start_commands, cromwell_server_command, run_commands
