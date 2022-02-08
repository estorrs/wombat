#!/bin/bash
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/cnv/C3L-00677/cromwell-workdir/logs
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/cnv:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/cnv /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/cnv/C3L-00677:/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/cnv/C3L-00677 /storage1/fs1/dinglab/Active:/storage1/fs1/dinglab/Active /storage1/fs1/m.wyczalkowski/Active:/storage1/fs1/m.wyczalkowski/Active /scratch1/fs1/dinglab/estorrs:/scratch1/fs1/dinglab/estorrs"
bgadd -L 10 /estorrs/test_cromwell
bsub -q dinglab-interactive -G compute-dinglab -a 'docker(mwyczalkowski/cromwell-runner)' -g /estorrs/test_cromwell -J 628df2c5-9dbb-4b5b-be14-aebfc4b51334 -Is '/bin/bash'