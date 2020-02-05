#!/bin/bash

#### overwrite ~/.aws/config
export AWS_DEFAULT_OUTPUT=text

##generating example-job.json, create-stream.json
# sh OtaEnvBuild.sh $your-binary $your-ota-role-arn $StreamID
sh OtaEnvBuild.sh $2 $3 $6 $7 | tee logfile

##Start Deploy Jobs
# sh OtaStressStart.sh $JobID $rounds $Jobs.JsonFile $StreamJsonFile $StreamID
sh OtaStressStart.sh $1 $4 $5 file://example-job.json  file://create-stream.json $6 | tee logfile