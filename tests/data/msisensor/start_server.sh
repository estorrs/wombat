#!/bin/bash
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/msisensor:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/msisensor /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/msisensor/C3L-01232:/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/msisensor/C3L-01232 /storage1/fs1/dinglab/Active:/storage1/fs1/dinglab/Active /storage1/fs1/m.wyczalkowski/Active:/storage1/fs1/m.wyczalkowski/Active"
bgadd -L 10 /estorrs/test_cromwell
bsub -q dinglab-interactive -G compute-dinglab -a 'docker(mwyczalkowski/cromwell-runner)' -Is '/bin/bash'