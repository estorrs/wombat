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
    is_list = False
    section_indent = None
    m = {}
    for line in f:
        indent = len(re.split(r'[^ ]', line)[0])
        if f'"{workflow_name}.cwl' in line:
            identifier = re.sub(r'^.*".*cwl.(.*)".*$', r'\1', line.strip())
            section_indent = indent
            # if output is a list of files
            is_list = '{[' in line.strip()
            if is_list:
                m[identifier] = []

        if '"location": ' in line and identifier is not None:
            location = re.sub(r'^.*location.*"(.*)".*$', r'\1', line.strip())
            if is_list and indent - 2 == section_indent:
                m[identifier].append(location)
            elif not is_list:
                m[identifier] = location
                identifier = None
                is_list = False

        if ']}' in line and is_list and indent == section_indent:
            identifier = None
            is_list = False

    return m


def get_step(filepath, workflow_name):
    return re.sub(r'^.*' + workflow_name + r'.cwl/[^/]*/call-([^/]*)/.*$', r'\1', filepath)


def get_pipeline_info(repo_root=None):
    old_cwd = os.getcwd()
    os.chdir(repo_root)
    # check to see if pecgs pipeline is in path
    commit_id = subprocess.check_output(('git', 'rev-parse', 'HEAD')).decode('utf-8').strip()
    version = subprocess.check_output(('git', 'describe', '--abbrev=0', '--tags')).decode('utf-8').strip()

    os.chdir(old_cwd)

    return commit_id, version
