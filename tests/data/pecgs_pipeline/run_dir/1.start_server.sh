#!/bin/bash
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/pecgs:/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/pecgs /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline /storage1/fs1/dinglab:/storage1/fs1/dinglab /storage1/fs1/m.wyczalkowski/Active:/storage1/fs1/m.wyczalkowski/Active /scratch1/fs1/dinglab:/scratch1/fs1/dinglab"
bsub -n 1 -q dinglab-interactive -G compute-dinglab -a 'docker(mwyczalkowski/cromwell-runner)' -Is '/bin/bash'