import os
import re
import subprocess


def listfiles(folder, regex=None):
    """Return all files with the given regex in the given folder structure"""
    for root, folders, files in os.walk(folder):
        for filename in folders + files:
            if regex is None:
                yield os.path.join(root, filename)
            elif re.findall(regex, os.path.join(root, filename)):
                yield os.path.join(root, filename)


def parse_output_from_log(log_fp, workflow_name):
    f = open(log_fp)
    identifier = None
    m = {}
    for line in f:
        line = line.strip()
        if f'"{workflow_name}.cwl' in line:
            identifier = re.sub(r'^.*".*cwl.(.*)".*$', r'\1', line)
        if '"location": ' in line and identifier is not None:
            location = re.sub(r'^.*location.*"(.*)".*$', r'\1', line)
            m[identifier] = location
            identifier = None
    return m


def get_step(filepath, workflow_name):
    return re.sub(r'^.*' + workflow_name + r'.cwl/[^/]*/call-([^/]*)/.*$', r'\1', filepath)


def get_pipeline_info():
    # check to see if pecgs pipeline is in path
    if '/pecgs-pipeline/' in os.getcwd():
        commit_id = subprocess.check_output(('git', 'rev-parse', 'HEAD')).decode('utf-8').strip()
        version = subprocess.check_output(('git', 'describe', '--abbrev=0', '--tags')).decode('utf-8').strip()
    else:
        print('WARNING: pecgs-pipeline is not in current working directory path. For pipeline commit_id and version to be correct, this command must be run from inside pecgs-pipeline repository. Setting dummy values for commit_id and version.')
        commit_id = 'dummy_commit_id'
        version = 'dummy_version'

    return commit_id, version
