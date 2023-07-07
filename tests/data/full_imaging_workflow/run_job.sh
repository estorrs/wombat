#!/bin/bash
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/full_imaging_workflow/cromwell-workdir/logs
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/full_imaging_workflow:/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/full_imaging_workflow /storage1/fs1/dinglab/Active/Projects/estorrs/multiplex-imaging-pipeline:/storage1/fs1/dinglab/Active/Projects/estorrs/multiplex-imaging-pipeline /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/full_imaging_workflow:/scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/full_imaging_workflow /storage1/fs1/dinglab:/storage1/fs1/dinglab /scratch1/fs1/dinglab:/scratch1/fs1/dinglab"
bgadd -L 10 /estorrs/test_cromwell
export PATH="/opt/java/openjdk/bin:$PATH"
bsub -R 'select[mem>10GB] rusage[mem=10GB] span[hosts=1]' -M 11GB -n 1 -q dinglab -G compute-dinglab -a 'docker(estorrs/cromwell-runner:58)' -g /estorrs/test_cromwell -J 669038e9-851a-4f6b-9012-f15f9557d0a4 -oo log.txt '/opt/java/openjdk/bin/java -Dconfig.file=/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/full_imaging_workflow/full_imaging_workflow.cromwell-config-db.compute1.dat -jar /app/cromwell-78-38cd360.jar run -t cwl -i /storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/full_imaging_workflow/inputs.yaml /storage1/fs1/dinglab/Active/Projects/estorrs/multiplex-imaging-pipeline/cwl/full_imaging_workflow.cwl'