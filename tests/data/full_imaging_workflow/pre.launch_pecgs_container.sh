#!/bin/bash
mkdir -p /scratch1/fs1/dinglab/estorrs/cromwell-data/pecgs/testing/full_imaging_workflow_multisample
export LSF_DOCKER_VOLUMES="/storage1/fs1/dinglab/Active:/storage1/fs1/dinglab/Active /scratch1/fs1/dinglab:/scratch1/fs1/dinglab"
export PATH="/miniconda/envs/mip/bin:$PATH"
bsub -q dinglab-interactive -G compute-dinglab -Is -a 'docker(estorrs/multiplex-imaging-pipeline:0.0.1)' '/bin/bash'