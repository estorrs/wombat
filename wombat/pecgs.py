import logging
import datetime
import os
import re
import uuid
import shutil
import yaml
from pathlib import Path

import pandas as pd

import wombat.bsub as bsub
import wombat.utils as utils


COMPUTE1_TN_WXS_FQ_DEFAULTS = os.path.join(
    Path(__file__).parent.absolute(), 'templates', 'compute1.defaults.pecgs_TN_wxs_fq.yaml')

COMPUTE1_TN_WXS_BAM_DEFAULTS = os.path.join(
    Path(__file__).parent.absolute(), 'templates', 'compute1.defaults.pecgs_TN_wxs_bam.yaml')

COMPUTE1_TN_WGS_BAM_DEFAULTS = os.path.join(
    Path(__file__).parent.absolute(), 'templates', 'compute1.defaults.pecgs_TN_wgs_bam.yaml')

COMPUTE1_T_RNA_FQ_DEFAULTS = os.path.join(
    Path(__file__).parent.absolute(), 'templates', 'compute1.defaults.pecgs_T_rna_fq.yaml')

DISEASE_TO_RESCUE_BED = {
    'PECGS': {
        'CHOL': os.path.join(Path(__file__).parent.absolute(), 'beds', 'pecgs_chol.bed'),
        'CRC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'pecgs_crc.bed'),
        'MM': os.path.join(Path(__file__).parent.absolute(), 'beds', 'pecgs_mm.bed'),
    },
    'TCGA': {
        'ACC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_ACC.bed'),
        'BLCA': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_BLCA.bed'),
        'BRCA': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_BRCA.bed'),
        'CESC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_CESC.bed'),
        'CHOL': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_CHOL.bed'),
        'COADREAD': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_COADREAD.bed'),
        'DLBC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_DLBC.bed'),
        'ESCA': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_ESCA.bed'),
        'GBM': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_GBM.bed'),
        'HNSC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_HNSC.bed'),
        'KICH': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_KICH.bed'),
        'KIRC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_KIRC.bed'),
        'KIRP': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_KIRP.bed'),
        'LAML': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_LAML.bed'),
        'LGG': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_LGG.bed'),
        'LIHC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_LIHC.bed'),
        'LUAD': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_LUAD.bed'),
        'LSCC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_LSCC.bed'),
        'LUSC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_LUSC.bed'),
        'MESO': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_MESO.bed'),
        'OV': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_OV.bed'),
        'PAAD': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_PAAD.bed'),
        'PANCAN': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_PANCAN.bed'),
        'PCPG': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_PCPG.bed'),
        'PRAD': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_PRAD.bed'),
        'SARC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_SARC.bed'),
        'SKCM': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_SKCM.bed'),
        'STAD': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_STAD.bed'),
        'TGCT': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_TGCT.bed'),
        'THCA': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_THCA.bed'),
        'THYM': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_THYM.bed'),
        'UCEC': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_UCEC.bed'),
        'UCS': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_UCSC.bed'),
        'UVM': os.path.join(Path(__file__).parent.absolute(), 'beds', 'driver_paper_UVM.bed'),
    }
}


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


def populate_defaults_TN_wxs_fq(
        sample, tumor_wxs_fq_1, tumor_wxs_fq_2,
        normal_wxs_fq_1, normal_wxs_fq_2,
        cpu=40, disease=''):
    d = {
        'sample': sample,
        'disease': disease,
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
    }

    d.update(yaml.safe_load(open(COMPUTE1_TN_WXS_FQ_DEFAULTS)))

    return d


def populate_defaults_TN_wxs_bam(
        sample, tumor_wxs_bam, normal_wxs_bam,
        cpu=40, disease=''):
    d = {
        'sample': sample,
        'disease': disease,
        'cpu': cpu,
        'tumor_wxs_bam': {
            'class': 'File',
            'path': tumor_wxs_bam
        },
        'normal_wxs_bam': {
            'class': 'File',
            'path': normal_wxs_bam
        },
    }

    d.update(yaml.safe_load(open(COMPUTE1_TN_WXS_BAM_DEFAULTS)))

    return d


def populate_defaults_TN_wgs_bam(tumor_wgs_bam, normal_wgs_bam):
    d = {
        'tumor_wgs_bam': {
            'class': 'File',
            'path': tumor_wgs_bam
        },
        'normal_wgs_bam': {
            'class': 'File',
            'path': normal_wgs_bam
        },
    }

    d.update(yaml.safe_load(open(COMPUTE1_TN_WGS_BAM_DEFAULTS)))

    return d


def populate_defaults_T_rna_fq(
        sample, tumor_rna_fq_1, tumor_rna_fq_2, cpu=40):
    d = {
        'sample': sample,
        'cpu': cpu,
        'tumor_rna_fq_1': {
            'class': 'File',
            'path': tumor_rna_fq_1
        },
        'tumor_rna_fq_2': {
            'class': 'File',
            'path': tumor_rna_fq_2
        },
        'bulk_expression_fq_1_list': [{
            'class': 'File',
            'path': tumor_rna_fq_1
        }],
        'bulk_expression_fq_2_list': [{
            'class': 'File',
            'path': tumor_rna_fq_2
        }],
    }

    d.update(yaml.safe_load(open(COMPUTE1_T_RNA_FQ_DEFAULTS)))

    return d


def generate_input_TN_wxs_fq(m, sequencing_info=None, cpu=40):
    d = populate_defaults_TN_wxs_fq(
        m['case_id'],
        m['wxs_tumor_R1'], m['wxs_tumor_R2'],
        m['wxs_normal_R1'], m['wxs_normal_R2'],
        cpu=cpu, disease=m['disease'])

    if sequencing_info is not None:
        d.update(get_sequencing_info(sequencing_info))

    return d


def generate_input_TN_wxs_bam(m, cpu=40):
    d = populate_defaults_TN_wxs_bam(
        m['case_id'],
        m['wxs_tumor_bam'], m['wxs_normal_bam'],
        cpu=cpu, disease=m['disease'])

    return d


def generate_input_TN_wgs_bam(m):
    d = populate_defaults_TN_wgs_bam(
        m['wgs_tumor_bam'], m['wgs_normal_bam'])

    return d


def generate_input_T_rna_fq(m, cpu=40):
    d = populate_defaults_T_rna_fq(
        m['case_id'],
        m['rna-seq_tumor_R1'], m['rna-seq_tumor_R2'],
        cpu=cpu)

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


def tidy_run(run_dir, script_fp):
    # check which runs are finished
    log_dir = os.path.join(run_dir, 'logs')
    log_fps = sorted(utils.listfiles(log_dir, regex='.log'))
    run_ids, execution_uuids = [], []
    for log_fp in log_fps:
        f = open(log_fp)
        run_id = None
        execution_uuid = None
        for line in f:
            if 'Successfully completed.' in line:
                # grab run name
                run_id = log_fp.split('/')[-1].replace('.log', '')
            matches = re.findall(r'cromwell-executions/[^/]+/([^/]+)/call', line)
            if matches:
                execution_uuid = matches[0]

        if run_id is not None:
            run_ids.append(run_id)
            execution_uuids.append(execution_uuid)

    # grab all inputs
    to_remove_pre = sorted(utils.listfiles(run_dir, regex=r'call-.*/inputs$'))
    to_remove_pre += sorted(utils.listfiles(run_dir, regex=r'call-stage.*staged_data.bam$'))

    # only keep if the jobs have finished already
    to_remove = []
    for fp in to_remove_pre:
        for run_id, ex_uuid in zip(run_ids, execution_uuids):
            if run_id in fp and ex_uuid in fp:
                to_remove.append(fp)
                break

    cmds = [f'rm -rf {fp}' for fp in to_remove]
    bsub.write_command_file(cmds, script_fp)

    return cmds


def generate_analysis_summary(tool_root, run_list, run_dir, workflow_name):
    # make run summary file
    run_list_fp = os.path.join(run_dir, 'runlist.txt')
    run_list.to_csv(run_list_fp, sep='\t')
    uuid_cols = [c for c in run_list.columns if '.uuid' in c]

    input_dir = os.path.join(run_dir, 'inputs')
    input_fps = sorted(utils.listfiles(input_dir, regex=r'.input.yaml$'))
    run_id_to_input_fp = {fp.split('/')[-1].split('.')[0]: fp
                          for fp in input_fps}

    log_dir = os.path.join(run_dir, 'logs')
    log_fps = sorted(utils.listfiles(log_dir, regex=r'.log$'))
    combined_analysis_summary = None
    run_summary = None
    run_data = []
    for log_fp in log_fps:
        # check to see if run is finished and completed sucessfully
        f = open(log_fp)
        completed = False
        for line in f:
            if 'Successfully completed.' in line:
                completed = True
                break

        if completed:
            run_id = log_fp.split('/')[-1].replace('.log', '')

            m = utils.parse_output_from_log(log_fp, workflow_name)

            data = []
            sample_id = run_list.loc[run_id, 'case_id']
            run_uuid = run_list.loc[run_id, 'run_uuid']
            run_date = str(datetime.datetime.today()).split(' ')[0]
            for k, v in m.items():
                if isinstance(v, list):
                    for item_index, item in enumerate(v):
                        result_uuid = str(uuid.uuid4())
                        data.append([
                            sample_id, utils.get_step(item, workflow_name),
                            f'{k}.{item_index}', item, os.path.getsize(item),
                            result_uuid, run_id, run_uuid, run_date])
                else:
                    result_uuid = str(uuid.uuid4())
                    data.append([
                        sample_id, utils.get_step(v, workflow_name), k, v, os.path.getsize(v),
                        result_uuid, run_id, run_uuid, run_date])
            analysis_summary = pd.DataFrame(
                data,
                columns=['case_id', 'workflow_step', 'result_name', 'data_path',
                               'filesize', 'result_uuid', 'run_id', 'run_uuid', 'run_date'])
            if combined_analysis_summary is None:
                combined_analysis_summary = analysis_summary
            else:
                combined_analysis_summary = pd.concat(
                    (combined_analysis_summary, analysis_summary), axis=0)

            commit_id, version = utils.get_pipeline_info(repo_root=tool_root)
            workflow_root = list(m.values())[0].split('/call-')[0]
            run_data.append([
                run_id, sample_id, run_uuid, run_date, workflow_name, version,
                commit_id, workflow_root, run_id_to_input_fp[run_id], log_fp,
                run_list_fp, ', '.join(run_list.loc[run_id, uuid_cols].to_list())])
    if run_data:
        run_summary = pd.DataFrame(
            data=run_data,
            columns=['run_id', 'case_id', 'run_uuid', 'run_date', 'pipeline_name',
                     'pipeline_version', 'pipeline_commit_id', 'run_root',
                     'run_input_config_filepath', 'run_log_filepath',
                     'runlist_filepath', 'run_input_uuids'])
    else:
        run_summary = None

    return combined_analysis_summary, run_summary


def from_run_list(
        run_list, run_dir, tool_root, pipeline_name,
        sequencing_info=None,
        job_group=None, n_concurrent=None, proxy_run_dir=None,
        input_kwargs=None, additional_volumes=None,
        queue='general'):
    log_dir = os.path.join(run_dir, 'logs')
    input_dir = os.path.join(run_dir, 'inputs')
    workflow_dir = os.path.join(run_dir, 'runs')

    if proxy_run_dir is None:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        Path(input_dir).mkdir(parents=True, exist_ok=True)
        Path(workflow_dir).mkdir(parents=True, exist_ok=True)
    print(sequencing_info)

    sequencing_info_map = generate_sequencing_info_map(sequencing_info) if sequencing_info is not None else None
    print(run_list)
    print(sequencing_info_map)

    inputs_fps, dconfigs, run_names = [], [], []
    for sample, d in run_list.items():
        if pipeline_name == 'pecgs_TN_wxs_fq':
            input = generate_input_TN_wxs_fq(
                d, sequencing_info_map.get(sample))
        elif pipeline_name == 'pecgs_TN_wxs_bam':
            input = generate_input_TN_wxs_bam(d)
        elif pipeline_name == 'pecgs_TN_wgs_bam':
            input = generate_input_TN_wgs_bam(d)
        elif pipeline_name == 'pecgs_T_rna_fq':
            input = generate_input_T_rna_fq(d)
        else:
            raise RuntimeError(f'{pipeline_name} is not a valid pipeline variant')

        if d['project'].upper() in DISEASE_TO_RESCUE_BED:
            if d['disease'].upper() in DISEASE_TO_RESCUE_BED[d['project'].upper()]:
                input['tindaisy_rescue_bed'] = DISEASE_TO_RESCUE_BED[d['project'].upper()][d['disease'].upper()]
            else:
                logging.info(d['project'] + ' has no bed file for ' + d['disease'] + '. Defaulting to pancan vaf rescue bed.')

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
            bsub.save_compute1_cromwell_template(
                workflow_root, template_fp, queue=queue)
        else:
            proxy_template_fp = os.path.join(
                proxy_input_dir, f'{sample}.cromwell-config-db.compute1.dat')
            bsub.save_compute1_cromwell_template(
                workflow_root, proxy_template_fp, queue=queue)

        dconfigs.append(template_fp)

        run_names.append(sample)

    server_fp = os.path.join(input_dir, 'server-cromwell-config.compute1.dat')

    cwl_fp = os.path.join(
        tool_root, 'cwl', 'pecgs_workflows', f'{pipeline_name}.cwl')
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
    filepath = os.path.join(system_run_dir, '1.run_jobs.sh')
    bsub.write_command_file(run_commands, filepath)

    return run_commands


def generate_launch_pecgs_env_cmds(run_dir, volumes=None):
    mkdir_cmd = f'mkdir -p {run_dir}'
    lsf_volumes = ['/storage1/fs1/dinglab/Active', '/scratch1/fs1/dinglab']
    if volumes is not None:
        lsf_volumes += volumes

    vol_str = ' '.join([f'{v}:{v}' for v in lsf_volumes])
    lsf_cmd = f'export LSF_DOCKER_VOLUMES="{vol_str}"'
    path_cmd = 'export PATH="/miniconda/envs/pecgs/bin:$PATH"'
    bsub_cmd = "bsub -q dinglab-interactive -G compute-dinglab -Is -a 'docker(estorrs/pecgs-pipeline:0.0.1)' '/bin/bash'"

    return [mkdir_cmd, lsf_cmd, path_cmd, bsub_cmd]


def generate_create_run_cmd(
        tool_root, pipeline_variant, run_list, run_dir,
        sequencing_info=None, queue='general'):
    fp = os.path.join(tool_root, 'src', 'compute1', 'generate_run_commands.py')
    pieces = [
        f'python {fp} make-run',
        f'--sequencing-info {sequencing_info}' if sequencing_info is not None else '',
        f'--queue {queue}',
        f'{pipeline_variant} {run_list} {run_dir}'
    ]
    cmd = ' '.join(pieces)
    return cmd


def generate_tidy_cmd(tool_root, pipeline_variant, run_list, run_dir):
    fp = os.path.join(tool_root, 'src', 'compute1', 'generate_run_commands.py')
    cmd = f'python {fp} tidy-run {pipeline_variant} {run_list} {run_dir}'
    return cmd


def generate_summarize_cmd(tool_root, pipeline_variant, run_list, run_dir):
    fp = os.path.join(tool_root, 'src', 'compute1', 'generate_run_commands.py')
    cmd = f'python {fp} summarize-run {pipeline_variant} {run_list} {run_dir}'
    return cmd


def generate_move_cmd(tool_root, pipeline_variant, run_list, run_dir, target_dir):
    fp = os.path.join(tool_root, 'src', 'compute1', 'generate_run_commands.py')
    cmd = f'python {fp} move-run {pipeline_variant} {run_list} {run_dir} --target-dir {target_dir}'
    return cmd


def create_run_setup_scripts(
        tool_root, out_dir, pipeline_variant, run_list, run_dir,
        volumes=None, sequencing_info=None, queue='general',
        target_dir=None):

    launch_cmds = generate_launch_pecgs_env_cmds(
        run_dir, volumes=volumes)
    make_cmd = generate_create_run_cmd(
        tool_root, pipeline_variant, run_list, run_dir,
        sequencing_info=sequencing_info, queue=queue)
    tidy_cmd = generate_tidy_cmd(
        tool_root, pipeline_variant, run_list, run_dir)
    summarize_cmd = generate_summarize_cmd(
        tool_root, pipeline_variant, run_list, run_dir)
    if target_dir is not None:
        move_cmd = generate_move_cmd(
            tool_root, pipeline_variant, run_list, run_dir, target_dir)

    filepath = os.path.join(out_dir, 'pre.launch_pecgs_container.sh')
    bsub.write_command_file(launch_cmds, filepath)
    filepath = os.path.join(out_dir, '1.make_run.sh')
    bsub.write_command_file([make_cmd], filepath)
    filepath = os.path.join(out_dir, '2.tidy_run.sh')
    bsub.write_command_file([tidy_cmd], filepath)
    filepath = os.path.join(out_dir, '3.summarize_run.sh')
    bsub.write_command_file([summarize_cmd], filepath)
    if target_dir is not None:
        filepath = os.path.join(out_dir, '4.move_run.sh')
        bsub.write_command_file([move_cmd], filepath)
    else:
        move_cmd = None

    return launch_cmds, make_cmd, tidy_cmd, summarize_cmd, move_cmd
