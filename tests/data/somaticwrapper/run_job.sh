#!/bin/bash
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/somaticwrapper/C3L-00677/cromwell-workdir/logs
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/somaticwrapper:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/somaticwrapper /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/somaticwrapper/C3L-00677:/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/somaticwrapper/C3L-00677 /storage1/fs1/dinglab:/storage1/fs1/dinglab /storage1/fs1/m.wyczalkowski:/storage1/fs1/m.wyczalkowski /scratch1/fs1/dinglab:/scratch1/fs1/dinglab"
bgadd -L 10 /estorrs/test_cromwell
export PATH="/opt/java/openjdk/bin:$PATH"
export PATH="/miniconda/envs/somaticwrapper/bin:$PATH"
bsub -R 'select[mem>10GB] rusage[mem=10GB] span[hosts=1]' -M 11GB -n 1 -q dinglab -G compute-dinglab -a 'docker(estorrs/cromwell-runner:58)' -g /estorrs/test_cromwell -J 43dd018a-c751-42d1-bb9b-73b40a031a47 -oo log.txt '/opt/java/openjdk/bin/java -Dconfig.file=/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/somaticwrapper/C3L-00677.cromwell-config-db.compute1.dat -jar /app/cromwell-78-38cd360.jar run -t cwl -i /storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/somaticwrapper/C3L-00677_inputs.yaml /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline/submodules/pecgs-somaticwrapper/cwl/somaticwrapper.cwl'