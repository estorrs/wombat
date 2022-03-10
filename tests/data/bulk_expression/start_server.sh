#!/bin/bash
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/bulk_expression/C3L-00677/cromwell-workdir/logs
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/bulk_expression:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/bulk_expression /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/bulk_expression/C3L-00677:/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/bulk_expression/C3L-00677 /storage1/fs1/dinglab/Active:/storage1/fs1/dinglab/Active /storage1/fs1/m.wyczalkowski/Active:/storage1/fs1/m.wyczalkowski/Active /scratch1/fs1/dinglab/estorrs:/scratch1/fs1/dinglab/estorrs"
bgadd -L 10 /estorrs/test_cromwell
bsub -n 1 -q dinglab-interactive -G compute-dinglab -a 'docker(mwyczalkowski/cromwell-runner)' -g /estorrs/test_cromwell -J e7a92807-f5ac-48e3-9ed9-c2e1fcd4f016 -Is '/bin/bash'