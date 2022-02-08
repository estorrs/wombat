#!/bin/bash
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/batch_cwl:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/batch_cwl /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline /storage1/fs1/dinglab/Active:/storage1/fs1/dinglab/Active /storage1/fs1/m.wyczalkowski/Active:/storage1/fs1/m.wyczalkowski/Active /scratch1/fs1/dinglab/estorrs:/scratch1/fs1/dinglab/estorrs"
bgadd -L 25 /estorrs/test_cromwell_hello
bsub -q dinglab-interactive -G compute-dinglab -a 'docker(mwyczalkowski/cromwell-runner)' -g /estorrs/test_cromwell_hello -J ab2e5b5a-705f-411f-b3c7-f6f62c0a10ef -Is '/bin/bash'