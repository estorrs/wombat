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


def bsub_command(command='/bin/bash', mem=10, max_mem=None, docker='python:3.8', queue='dinglab',
                        group='compute-dinglab', group_name=None, job_name=None, interactive=False,
                        n_processes=1, username='estorrs', log_fp=None):

    if max_mem is None:
        max_mem = mem

    if interactive and queue != f'{queue}-interactive':
        queue = f'{queue}-interactive'

    base = f'bsub'
    if mem is not None:
        base += f' -R \'rusage[mem={mem}GB]\' -M {max_mem}GB'

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


def housekeeping_priors(log_dir, args, volumes=None):
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
    java_export_cmd = f'export PATH="/opt/java/openjdk/bin:$PATH"'


    return mv_command, jg_command, java_export_cmd


def batch_bsub_commands(commands, job_names, log_dir, args, volumes=None):
    mv_command, jg_command, java_export_cmd = housekeeping_priors(log_dir, args, volumes=volumes)

    bsub_commands = []
    for command, job_name in zip(commands, job_names):
        log_fp = os.path.join(log_dir, f'{job_name}.txt')

        c = bsub_command(
            command=command, mem=args['mem'], max_mem=args['max_mem'],
            docker=args['docker'], queue=args['queue'], group=args['group'],
            group_name=args['group_name'], job_name=job_name, interactive=args['interactive'],
            n_processes=args['n_processes'], log_fp=log_fp, username=args['username'])

        bsub_commands.append(c)

    all_commands = [c for c in [f'mkdir -p {log_dir}', mv_command, jg_command, java_export_cmd]
                    if c is not None]
    all_commands += bsub_commands

    return all_commands


def submit_cwl_command(dconfig, cwl_fp, inputs_fp, java='/opt/java/openjdk/bin/java',
                       jar='/app/cromwell-78-38cd360.jar'):
    cmd = f'{java} -Dconfig.file={dconfig}'
#     cmd += ' -Djavax.net.ssl.trustStorePassword=changeit -Djavax.net.ssl.trustStore=/gscmnt/gc2560/core/genome/cromwell/cromwell.truststore'
    cmd += f' -jar {jar} run -t cwl -i {inputs_fp} {cwl_fp}'
    return cmd


def create_cromwell_workdir_command(workflow_root):
    cmd = f'mkdir -p {workflow_root}/cromwell-workdir/logs'
    return cmd


def cromwell_commands(dconfig, cwl_fp, inputs_fp, args, volumes, workflow_root=None):
    mv_command, jg_command, java_export_cmd = housekeeping_priors(None, args, volumes=volumes)
    mh_command = map_host_command()
    source_lsf_command = 'source /opt/ibm/lsfsuite/lsf/conf/lsf.conf'

    start_server_command = bsub_command(
            command='/bin/bash', group=args['group'], group_name=args['group_name'], mem=None,
            docker='broadinstitute/cromwell:78-38cd360', queue=args['queue'], interactive=True)

    submit_command = submit_cwl_command(dconfig, cwl_fp, inputs_fp)

    start_docker_commands = []
    if workflow_root is not None:
        start_docker_commands += [create_cromwell_workdir_command(workflow_root)]
    start_docker_commands += [c for c in [source_lsf_command, mh_command, mv_command, jg_command, java_export_cmd, start_server_command]
                              if c is not None]
    return start_docker_commands, submit_command


def start_cromwell_server_command(
        dconfig, java='/opt/java/openjdk/bin/java', jar='/app/cromwell-78-38cd360.jar'):
    cmd = f'{java} -Dconfig.file={dconfig}'
    cmd += f' -jar {jar} server'
    return cmd


def batch_cromwell_commands(dconfigs, server_config, cwl_fp, inputs_fps,
                            run_names, log_dir, run_dir,
                            args, volumes):
    mv_command, jg_command = housekeeping_priors(None, args, volumes=volumes)
    mh_command = map_host_command()
    source_lsf_command = 'source /opt/ibm/lsfsuite/lsf/conf/lsf.conf'

    start_server_command = bsub_command(
            command='/bin/bash', group=args['group'], group_name=args['group_name'], mem=None,
            docker='broadinstitute/cromwell:78-38cd360', queue=args['queue'], interactive=True)

    start_cromwell_command = start_cromwell_server_command(server_config)

    submit_commands = [submit_cwl_command(dconfig, cwl_fp, fp)
                       for fp, name, dconfig in zip(inputs_fps, run_names, dconfigs)]
    submit_commands = [bsub_command(
                           command=cmd, group=args['group'], group_name=args['group_name'],
                           job_name=f'cromwell_launch_{name}', mem=None, docker='broadinstitute/cromwell:78-38cd360',
                           queue=args['queue'], interactive=False,
                           log_fp=os.path.join(log_dir, f'{name}.log'))
                       for cmd, name in zip(submit_commands, run_names)]
    submit_commands = [c for c in [source_lsf_command, mh_command, mv_command]
                       if c is not None] + submit_commands

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
