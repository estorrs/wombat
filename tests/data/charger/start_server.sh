#!/bin/bash
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/charger/C3L-00081/cromwell-workdir/logs
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/charger:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/charger /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/charger/C3L-00081:/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/charger/C3L-00081 /storage1/fs1/dinglab/Active:/storage1/fs1/dinglab/Active /storage1/fs1/m.wyczalkowski/Active:/storage1/fs1/m.wyczalkowski/Active /scratch1/fs1/dinglab/estorrs:/scratch1/fs1/dinglab/estorrs"
bgadd -L 10 /estorrs/test_cromwell
export PATH="/opt/java/openjdk/bin:$PATH"
bsub -n 1 -q general-interactive -G compute-dinglab -a 'docker(estorrs/cromwell-runner:58)' -g /estorrs/test_cromwell -J 6fb4f546-f5c9-46bd-9bed-ecc3e8c1ee0e -Is '/bin/bash'