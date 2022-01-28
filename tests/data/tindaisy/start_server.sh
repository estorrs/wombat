#!/bin/bash
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/tindaisy:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/tindaisy /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline/submodules/TinDaisy/:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline/submodules/TinDaisy/ /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/tindaisy/C3L-01232:/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/tindaisy/C3L-01232 /storage1/fs1/dinglab/Active:/storage1/fs1/dinglab/Active"
bgadd -L 10 /estorrs/test_cromwell
bsub -q dinglab-interactive -G compute-dinglab -a 'docker(mwyczalkowski/cromwell-runner)' -Is '/bin/bash'