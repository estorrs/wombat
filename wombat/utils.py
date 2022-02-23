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
    output = subprocess.check_output(('git', 'log', '-1')).decode('utf-8').split('\n')[0]
    commit_id = re.sub(r'^commit\s(.*)\s.*$', r'\1', output)
    version = re.sub(r'^commit\s.*tag:\s(),\s.*$', r'\1', output)
    return commit_id, version
