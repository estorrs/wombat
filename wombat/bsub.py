import os
import re
import uuid
from pathlib import Path


DEFAULT_ARGS = {
    'mem': 10,
    'n_processes': 1,
    'max_mem': None,
    'docker': 'python:3.8',
    'queue': 'dinglab',
    'gpu_model': 'TeslaV100_SXM2_32GB',
    'gpu_mem': '30',
    'gpu_num': 1,
    'use_gpu': False,
    'group': 'compute-dinglab',
    'group_name': None,
    'n_concurrent': 10,
    'interactive': False,
    'username': 'estorrs'
}


DEFAULT_CROMWELL_TEMPLATE = os.path.join(
    Path(__file__).parent.absolute(), 'templates', 'cromwell-config-db.compute1.template.dat')

# DEFAULT_CROMWELL_SERVER_TEMPLATE = os.path.join(
#     Path(__file__).parent.absolute(), 'templates', 'server-cromwell-config.compute1.dat')


def map_host_command(h='host'):
    return f'export LSF_DOCKER_NETWORK={h}'


def map_volumes_command(dirs):
    vol_str = ' '.join(
        [f'{d}:{d}' for d in dirs]
    )
    return f'export LSF_DOCKER_VOLUMES="{vol_str}"'


def create_job_group_command(group_name,  n=10, username='estorrs'):
    return f'bgadd -L {n} /{username}/{group_name}'


def job_group_status_command(group_name, username='estorrs'):
    return f'bjgroup -s /{username}/{group_name}'


def bsub_command(command='/bin/bash', mem=10, max_mem=11, hosts=1, docker='python:3.8', queue='dinglab',
                group='compute-dinglab', group_name=None, job_name=None, interactive=False,
                n_processes=1, username='estorrs', log_fp=None,
                gpu_model='TeslaV100_SXM2_32GB', gpu_mem=30, gpu_num=1, use_gpu=False):

    if max_mem is None:
        max_mem = mem

    if interactive and queue != f'{queue}-interactive':
        queue = f'{queue}-interactive'

    base = f'bsub'
    if use_gpu:
        base += f' -R \'select[gpuhost,mem>{mem}GB] rusage[mem={mem}GB] span[hosts={hosts}]\' -M {max_mem}GB -gpu \'num={gpu_num}:gmodel={gpu_model}:gmem={gpu_mem}GB\''
    else:
        base += f' -R \'select[mem>{mem}GB] rusage[mem={mem}GB] span[hosts={hosts}]\' -M {max_mem}GB'

    if n_processes is not None:
        base += f' -n {n_processes}'

    if queue is not None:
        base += f' -q {queue}'

    if group is not None:
        base += f' -G {group}'

    if docker is not None:
        base += f' -a \'docker({docker})\''

    if group_name is not None:
        job_name = str(uuid.uuid4()) if job_name is None else job_name
        base += f' -g /{username}/{group_name} -J {job_name}'

    if log_fp is not None:
        base += f' -oo {log_fp}'

    if interactive:
        base += ' -Is'

    if command is not None:
        base += f' \'{command}\''

    return base


def housekeeping_priors(log_dir, args, volumes=None, exports=None):
    if volumes is None:
        volumes = []

    if log_dir is not None:
        if log_dir not in volumes:
            volumes.append(log_dir)

    if volumes:
        mv_command = map_volumes_command(volumes)
    else:
        mv_command = None

    if args['group_name'] is not None:
        jg_command = create_job_group_command(
            args['group_name'],  n=args['n_concurrent'], username=args['username'])
    else:
        jg_command = None


    # make sure java in broad cromwell container is visible
    # plus additional exports if specified
    ls = ['/opt/java/openjdk/bin']
    if exports is not None:
        ls += exports
    export_cmd = f'export PATH="' + ':'.join(ls) + ':$PATH"'

    return mv_command, jg_command, export_cmd


def batch_bsub_commands(commands, job_names, log_dir, args, volumes=None, sleep=None,
                        export_java=True, exports=None):
    if args['max_mem'] is None:
        args['max_mem'] = args['mem'] + 1

    if volumes is None:
        volumes = ['/storage1/fs1/dinglab', '/scratch1/fs1/dinglab', '/home/' + args['username']]

    mv_command, jg_command, java_export_cmd = housekeeping_priors(log_dir, args, volumes=volumes, exports=exports)

    bsub_commands = []
    for command, job_name in zip(commands, job_names):
        log_fp = os.path.join(log_dir, f'{job_name}.txt')

        c = bsub_command(
            command=command, mem=args['mem'], max_mem=args['max_mem'],
            docker=args['docker'], queue=args['queue'], group=args['group'],
            group_name=args['group_name'], job_name=job_name, interactive=args['interactive'],
            n_processes=args['n_processes'], log_fp=log_fp, username=args['username'],
            gpu_model=args['gpu_model'], gpu_mem=args['gpu_mem'],
            gpu_num=args['gpu_num'], use_gpu=args['use_gpu'])

        bsub_commands.append(c)

        # prevent database/server overload errors
        if sleep is not None:
            bsub_commands.append(f'sleep {sleep}')

    all_commands = [c for c in [f'mkdir -p {log_dir}', mv_command, jg_command]
                    if c is not None]
    if export_java:
        all_commands.append(java_export_cmd)
    all_commands += bsub_commands

    return all_commands


def submit_cwl_command(dconfig, cwl_fp, inputs_fp, java='/opt/java/openjdk/bin/java',
                       jar='/app/cromwell-78-38cd360.jar'):
    cmd = f'{java} -Dconfig.file={dconfig}'
    cmd += f' -jar {jar} run -t cwl -i {inputs_fp} {cwl_fp}'
    return cmd


def create_cromwell_workdir_command(workflow_root):
    cmd = f'mkdir -p {workflow_root}/cromwell-workdir/logs'
    return cmd


def cromwell_commands(dconfig, cwl_fp, inputs_fp, args, volumes,
        workflow_root=None, interactive=False, log_fp=None):
    mv_command, jg_command, java_export_cmd = housekeeping_priors(None, args, volumes=volumes)
    mh_command = map_host_command()
    source_lsf_command = 'source /opt/ibm/lsfsuite/lsf/conf/lsf.conf'

    start_server_command = bsub_command(
            command='/bin/bash', group=args['group'], group_name=args['group_name'], mem=None,
            docker='estorrs/cromwell-runner:58', queue=args['queue'], interactive=True)

    submit_command = submit_cwl_command(dconfig, cwl_fp, inputs_fp)

    start_docker_commands = []
    if workflow_root is not None:
        start_docker_commands += [create_cromwell_workdir_command(workflow_root)]
    start_docker_commands += [c for c in [source_lsf_command, mh_command, mv_command, jg_command, java_export_cmd, start_server_command]
                              if c is not None]
    
    if interactive:
        return start_docker_commands, submit_command
    
    cmd = bsub_command(
        command=submit_command, group=args['group'], group_name=args['group_name'], mem=None,
        docker='estorrs/cromwell-runner:58', queue=args['queue'], interactive=False, log_fp=log_fp)
    return start_docker_commands[:-1] + [cmd]


def start_cromwell_server_command(
        dconfig, java='/opt/java/openjdk/bin/java', jar='/app/cromwell-78-38cd360.jar'):
    cmd = f'{java} -Dconfig.file={dconfig}'
    cmd += f' -jar {jar} server'
    return cmd


def batch_cromwell_commands(dconfigs, server_config, cwl_fp, inputs_fps,
                            run_names, log_dir, run_dir,
                            args, volumes, sleep=None):
    mv_command, jg_command, java_export_cmd = housekeeping_priors(None, args, volumes=volumes)
    mh_command = map_host_command()
    source_lsf_command = 'source /opt/ibm/lsfsuite/lsf/conf/lsf.conf'

    start_server_command = bsub_command(
            command='/bin/bash', group=args['group'], group_name=args['group_name'], mem=None,
            docker='estorrs/cromwell-runner:58', queue=args['queue'], interactive=True)

    start_cromwell_command = start_cromwell_server_command(server_config)

    submit_commands = [submit_cwl_command(dconfig, cwl_fp, fp)
                       for fp, name, dconfig in zip(inputs_fps, run_names, dconfigs)]
    cmds = []
    for cmd, name in zip(submit_commands, run_names):
        cmd = bsub_command(command=cmd, group=args['group'], group_name=args['group_name'],
                           job_name=f'cromwell_launch_{name}', mem=None, docker='estorrs/cromwell-runner:58',
                           queue=args['queue'], interactive=False,
                           log_fp=os.path.join(log_dir, f'{name}.log'))
        cmds.append(cmd)
        if sleep is not None:
            cmds.append(f'sleep {sleep}')

    submit_commands = [c for c in [source_lsf_command, mh_command, mv_command, java_export_cmd]
                       if c is not None] + cmds

    submit_commands = [f'mkdir -p {log_dir}'] + [
        create_cromwell_workdir_command(os.path.join(run_dir, name)) for name in run_names] + submit_commands

    start_docker_commands = [c for c in [source_lsf_command, mh_command, mv_command, jg_command, start_server_command]
                             if c is not None]
    return start_docker_commands, start_cromwell_command, submit_commands


def save_compute1_cromwell_template(workflow_root, output_fp, queue='general'):
    f = open(DEFAULT_CROMWELL_TEMPLATE)
    lines = []
    for line in f:
        lines.append(line.replace('\n', ''))
    f.close()

    lines = [l.replace('WORKFLOW_ROOT', workflow_root) for l in lines]
    lines = [l.replace('-q general', f'-q {queue}') for l in lines]

    f = open(output_fp, 'w')
    f.write('\n'.join(lines))
    f.close()


def write_command_file(commands, filepath):
    root = '/'.join(filepath.split('/')[:-1])
    Path(root).mkdir(parents=True, exist_ok=True)

    f = open(filepath, 'w')
    f.write('#!/bin/bash\n')
    f.write('\n'.join(commands))
    f.close()
