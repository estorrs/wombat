#!/bin/bash
/usr/bin/java -Dconfig.file=/storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/cnv/C3L-00677.cromwell-config-db.compute1.dat -Djavax.net.ssl.trustStorePassword=changeit -Djavax.net.ssl.trustStore=/gscmnt/gc2560/core/genome/cromwell/cromwell.truststore -jar /usr/local/cromwell/cromwell-47.jar run -t cwl -i /storage1/fs1/dinglab/Active/Projects/estorrs/wombat/tests/data/cnv/C3L-00677_inputs.yaml /storage1/fs1/dinglab/Active/Projects/estorrs/pecgs-pipeline/submodules/pecgs-cnv/cwl/cnv.cwl