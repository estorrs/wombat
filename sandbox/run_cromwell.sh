#!/bin/bash
source /opt/ibm/lsfsuite/lsf/conf/lsf.conf
export LSF_DOCKER_NETWORK=host
export LSF_DOCKER_VOLUMES="/path/to/dira:/path/to/dira /path/to/dir/b:/path/to/dir/b /path/to/log_dir:/path/to/log_dir"
bgadd -L 10 /estorrs/test_group
bsub -q dinglab-interactive -a 'docker(mwyczalkowski/cromwell-runner)' -Is
/usr/bin/java -Dconfig.file=dat/cromwell-config-db.compute1.dat -Djavax.net.ssl.trustStorePassword=changeit -Djavax.net.ssl.trustStore=/gscmnt/gc2560/core/genome/cromwell/cromwell.truststore -jar /usr/local/cromwell/cromwell-47.jar -t cwl -i dat/C3N-02996.BIOTEXT_YEyWzRW.yaml ../../cwl/workflows/tindaisy2.cwl