#!/bin/bash

#### parameter initicalization #####
binName=$1
RoleARN=$2
binFile="$PWD/$binName"
version=1
fileSize=$( wc -c "${binFile}" |awk -F " " '{print $1}' )

s3Key=""
streamId=$3
fileId=$( od -An -N1 -i /dev/random | head -1 |sed 's/[[:space:]]//g' )
Rand=$( od -An -N3 -i /dev/random | head -1 |sed 's/[[:space:]]//g' )
#### handling md5 sum ######
md5sum=123
if [[ "$OSTYPE" == "linux-gnu" ]]; then #Linux
        md5sum=$(md5sum "${binFile}" | awk '{ print $4 }')
elif [[ "$OSTYPE" == "darwin"* ]]; then #MAC OS
        md5sum=$(md5 "${binFile}" | awk '{ print $4 }')
fi


#### check if S3 OTA usage bucket exists, if not create one for it #####

s3Bucket=iot-ota-upgrade-package-${Rand} ### S3 bucket name needs to be unique
echo ${s3Bucket}

bucketName=$( aws s3 ls | grep iot-ota-upgrade-package |awk -F " " '{print $3}')
s3Key=${fileId}/${binName}
if [ -z "$bucketName" ]
    then
        aws s3 mb s3://${s3Bucket}
    else
        s3Bucket=$bucketName
fi

aws s3 cp ${binName} s3://${s3Bucket}/${s3Key}

#### create stream file ####
cat > ${PWD}/create-stream.json << EOF
{
    "streamId": "${streamId}",
    "description": "This stream is used for sending ${version} ota stream file to devices.",
    "files": [
        {
            "fileId": ${fileId},
            "s3Location": {
                "bucket": "${s3Bucket}",
                "key": "${s3Key}"
            }
        }
    ],
    "roleArn": "${RoleARN}"
}
EOF
cat create-stream.json
## create job file
cat > ${PWD}/example-job.json << EOF
{
    "command": "fota",
    "streamId": "${streamId}",
    "fileId": ${fileId},
    "fileSize": ${fileSize},
    "imageVer": "${version}",
    "md5sum": "${md5sum}"
}
cat example-job.json
EOF
