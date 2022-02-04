import os
import re
import uuid
from pathlib import Path


DEFAULT_ARGS = {
    'mem': 10,
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
                        username='estorrs', log_fp=None):

    if max_mem is None:
        max_mem = mem

    if interactive and queue != f'{queue}-interactive':
        queue = f'{queue}-interactive'

    base = f'bsub'
    if mem is not None:
        base += f' -R \'rusage[mem={mem}GB]\' -M {max_mem}GB'

    if queue is not None:
        base += f' -q {queue}'

    if group is not None:
        base += f' -G {group}'

    if docker is not None:
        base += f' -a \'docker({docker})\''

    if group_name is not None:
        job_name = str(uuid.UUID4()) if job_name is None else job_name
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
        try:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        except:
            print(f'Failed to create log dir {log_dir}')

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

    return mv_command, jg_command


def batch_bsub_commands(commands, job_names, log_dir, args, volumes=None):
    mv_command, jg_command = housekeeping_priors(log_dir, args, volumes=volumes)

    bsub_commands = []
    for command, job_name in zip(commands, job_names):
        log_fp = os.path.join(log_dir, f'{job_name}.txt')

        c = bsub_command(
            command=command, mem=args['mem'], max_mem=args['max_mem'],
            docker=args['docker'], queue=args['queue'], group=args['group'],
            group_name=args['group_name'], job_name=job_name, interactive=args['interactive'],
            log_fp=log_fp, username=args['username'])

        bsub_commands.append(c)

    all_commands = [c for c in [mv_command, jg_command]
                    if c is not None]
    all_commands += bsub_commands

    return all_commands


def submit_cwl_command(dconfig, cwl_fp, inputs_fp, java='/usr/bin/java',
                       jar='/usr/local/cromwell/cromwell-47.jar'):
    cmd = f'{java} -Dconfig.file={dconfig}'
    cmd += ' -Djavax.net.ssl.trustStorePassword=changeit -Djavax.net.ssl.trustStore=/gscmnt/gc2560/core/genome/cromwell/cromwell.truststore'
    cmd += f' -jar {jar} run -t cwl -i {inputs_fp} {cwl_fp}'
    return cmd


def cromwell_commands(dconfig, cwl_fp, inputs_fp, args, volumes):
    mv_command, jg_command = housekeeping_priors(None, args, volumes=volumes)
    mh_command = map_host_command()
    source_lsf_command = 'source /opt/ibm/lsfsuite/lsf/conf/lsf.conf'

    start_server_command = bsub_command(
            command='/bin/bash', group=args['group'], mem=None,
            docker='mwyczalkowski/cromwell-runner', queue=args['queue'], interactive=True)

    submit_command = submit_cwl_command(dconfig, cwl_fp, inputs_fp)

    start_docker_commands = [c for c in [source_lsf_command, mh_command, mv_command, jg_command, start_server_command]
                    if c is not None]
    return start_docker_commands, submit_command


def save_compute1_cromwell_template(workflow_root, output_fp):
    f = open(DEFAULT_CROMWELL_TEMPLATE)
    lines = []
    for line in f:
        lines.append(line.replace('\n', ''))
    f.close()

    lines = [l.replace('WORKFLOW_ROOT', workflow_root) for l in lines]

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
