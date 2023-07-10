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

COMPUTE1_FULL_IMAGING_DEFAULTS = os.path.join(
    Path(__file__).parent.absolute(), 'templates', 'compute1.defaults.full_imaging_workflow.yaml')

def populate_defaults_full_imaging(
        specimen_id, input_tif, nuclei_channels='DAPI',
        membrane_channels='Pan-Cytokeratin,E-cadherin,CD45,CD8,CD3e,CD4,Vimentin,SMA,CD31',
        mask_markers='Pan-Cytokeratin,E-cadherin',
        group='HTAN', project='Multiplex_Imaging',
        bbox=None, platform='phenocycler'):
    d = {
        'specimen_id': specimen_id,
        'input_tif': {
            'class': 'File',
            'path': input_tif
        },
        'platform': platform,
        'bbox': bbox,
        'nuclei_channels': nuclei_channels,
        'membrane_channels': membrane_channels,
        'mask_markers': mask_markers,
        'group': group,
        'project': project,
    }

    d.update(yaml.safe_load(open(COMPUTE1_FULL_IMAGING_DEFAULTS)))

    return d


def generate_input_full_imaging(m):
    kwargs = {}
    for k, v in m.items():
        if not pd.isnull(v) and k not in ['specimen_id', 'input_tif']:
            kwargs[k] = v

    d = populate_defaults_full_imaging(
        m['specimen_id'],
        m['input_tif'], **kwargs)

    return d


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
            sample_id = run_list.loc[run_id, 'specimen_id']
            run_date = str(datetime.datetime.today()).split(' ')[0]
            for k, v in m.items():
                if isinstance(v, list):
                    for item_index, item in enumerate(v):
                        result_uuid = str(uuid.uuid4())
                        data.append([
                            sample_id, utils.get_step(item, workflow_name),
                            f'{k}.{item_index}', item, os.path.getsize(item),
                            result_uuid, run_id, run_date])
                else:
                    result_uuid = str(uuid.uuid4())
                    data.append([
                        sample_id, utils.get_step(v, workflow_name), k, v, os.path.getsize(v),
                        result_uuid, run_id, run_date])
            analysis_summary = pd.DataFrame(
                data,
                columns=['specimen_id', 'workflow_step', 'result_name', 'data_path',
                               'filesize', 'result_uuid', 'run_id', 'run_date'])
            if combined_analysis_summary is None:
                combined_analysis_summary = analysis_summary
            else:
                combined_analysis_summary = pd.concat(
                    (combined_analysis_summary, analysis_summary), axis=0)

            commit_id, version = utils.get_pipeline_info(repo_root=tool_root)
            workflow_root = list(m.values())[0].split('/call-')[0]
            run_data.append([
                run_id, sample_id, run_date, workflow_name, version,
                commit_id, workflow_root, run_id_to_input_fp[run_id], log_fp,
                run_list_fp])
    if run_data:
        run_summary = pd.DataFrame(
            data=run_data,
            columns=['run_id', 'case_id', 'run_date', 'pipeline_name',
                     'pipeline_version', 'pipeline_commit_id', 'run_root',
                     'run_input_config_filepath', 'run_log_filepath',
                     'runlist_filepath'])
    else:
        run_summary = None

    return combined_analysis_summary, run_summary


def from_run_list(
        run_list, run_dir, tool_root, pipeline_name,
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

    inputs_fps, dconfigs, run_names = [], [], []
    for sample, d in run_list.items():
        if pipeline_name == 'full_imaging_workflow':
            input = generate_input_full_imaging(d)
        # elif pipeline_name == 'x':
        #     input = generate_input_x(d)
        else:
            raise RuntimeError(f'{pipeline_name} is not a valid pipeline variant')

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
        tool_root, 'cwl', f'{pipeline_name}.cwl')
    volumes = [re.sub(r'^(.*)/$', r'\1', run_dir), re.sub(r'^(.*)/$', r'\1', tool_root),
               '/storage1/fs1/dinglab', '/storage1/fs1/m.wyczalkowski/Active',
               '/scratch1/fs1/dinglab']
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
    path_cmd = 'export PATH="/miniconda/envs/mip/bin:$PATH"'
    bsub_cmd = "bsub -q dinglab-interactive -G compute-dinglab -Is -a 'docker(estorrs/multiplex-imaging-pipeline:0.0.1)' '/bin/bash'"

    return [mkdir_cmd, lsf_cmd, path_cmd, bsub_cmd]


def generate_create_run_cmd(
        tool_root, pipeline_variant, run_list, run_dir,
        sequencing_info=None, queue='general'):
    fp = os.path.join(tool_root, 'src', 'compute1', 'generate_run_commands.py')
    pieces = [
        f'python {fp} make-run', f'--queue {queue}',
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
