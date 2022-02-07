#!/bin/bash
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/batch_cwl/logs
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/batch_cwl/0/cromwell-workdir/logs
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/batch_cwl/1/cromwell-workdir/logs
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/batch_cwl/2/cromwell-workdir/logs
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/batch_cwl/3/cromwell-workdir/logs
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/batch_cwl/4/cromwell-workdir/logs
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/batch_cwl:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/batch_cwl /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline /storage1/fs1/dinglab/Active:/storage1/fs1/dinglab/Active /storage1/fs1/m.wyczalkowski/Active:/storage1/fs1/m.wyczalkowski/Active /scratch1/fs1/dinglab/estorrs:/scratch1/fs1/dinglab/estorrs"
bgadd -L 25 /estorrs/test_cromwell
bsub -q dinglab-interactive -G compute-dinglab -a 'docker(mwyczalkowski/cromwell-runner)' -g /estorrs/test_cromwell -J e0aac8fa-d888-4b10-9436-1ec353dd3301 -Is '/bin/bash'