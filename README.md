# AWS IoT OTA deployment tool user manual

This document describes tools that can be used for deploying over-the-air (OTA) firmware updates on AWS IoT. The tools can be used for testing OTA firmware updates as well. 

# Contents

* **Deploy OTA firmware updates using shell scripts**
* **Deploy OTA firmware updates using python**

# Deploy OTA firmware updates using shell scripts:

## Description:

In the first section we will go through how to setup stress test by using the shell scripts.

## Prerequisites:

1. you need to have AWS account

1. Install[AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)and [configure](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

1. Create IAM user maker sure it has [OTA required user policy](https://docs.aws.amazon.com/freertos/latest/userguide/create-ota-user-policy.html)
2. [Create an OTA update service role](https://docs.aws.amazon.com/freertos/latest/userguide/create-service-role.html)

## Usage:

### List down the devices that will be update through OTA 

There are many ways to filter out the target devices of interest. 

1. you can create a group of your devices by [AWS IoT Device Management](https://docs.aws.amazon.com/iot/latest/developerguide/thing-groups.html) and use [AWS CLI to describe the ARN of the group](https://docs.aws.amazon.com/cli/latest/reference/iot/describe-thing-group.html), then copy the ARN to thingList.txt
2. you can also [list down the devices one by one with AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/iot/describe-thing.html) and copy the ARN to thingList.txt


After listed down the devices, your thingList.txt file should look like this :

![](./docs/thinglist.png)
## Running main.sh 

sh main.sh <ThingListFile> <BinFile> <RoleARN > <JobID> <Rounds> <StreamID>

**Description:**

main.sh creates the job,stream documents, upload the bin file to S3, parse the thingLists.txt and then starts a deployment or repeated stress test with the parameters

* ThingListFile:
    *  for example Thinglist.txt like the above example
* BinFile:  
    * the binary that you wish to update, it will be uploaded to S3 by the script durring the test
* RoleARN: 
    * the ota role you’ve created, it should look like “**arn:aws:iam::123456789:role/your_ota_role**“ and given [OTA update service role](https://docs.aws.amazon.com/freertos/latest/userguide/create-service-role.html) access
* JobID:
    * input the job id you would like to use in the test, and you can track the status on IoT Console, the job will be deleted after the test is completed. 
* Rounds:
    * when you use this tool for deploying an OTA firmware update, set this value to 1. Use a value larger than 1 for repeated testing purpose. This tool will deploy the same OTA job repeatedly for $Rounds times; if failure happens, the deployment will stop and the rest of the $Rounds will be skipped.
* StreamID:
    * input the stream id you would like to use in the test. The stream will be deleted after the test is completed. 

### Example:

```
sh main.sh thingsList.txt test.bin arn:aws:iam::<$your_aacount>:role/your_role TestJob1234 3 TestStream1234
```

![](./docs/log_example.png)

## Customizing your test

If you use the main.sh script above, it creates json files to describe the job and the stream for you automatically. Your device must be able to handle those specific format. If you need flexibility in defining your own format to match implementation on the device, you can follow the instructions in this section, then run OtaStressStart.sh.

### Template Example:

job document

```
{
    "command": "fota",
    "streamId": "TestStream55667788",
    "fileId": 69,
    "fileSize": 382432,
    "imageVer": "1",
    "md5sum": "afcba86284d600cd21f54dca7c6d8bb6"
}

```

```
    "streamId": "fota-image-v1-stream",
    "fileId": *any_integer_between_0_to_255*,
    "fileSize": *your_fota_image_size_in_Bytes*
```


**command:**

A command name that the device will handle and will react to start the download agent

**streamId:**

The stream ID.
Length Constraints: Minimum length of 1. Maximum length of 128.

[**fileId:**](https://docs.aws.amazon.com/iot/latest/apireference/API_CreateStream.html#API_CreateStream_RequestSyntax)

The fileId to stream, it should consistent to the fileId in the stream document

**fileSize:**

The file size of the ota bin file

**imageVer:**

the image version of the ota bin file

**md5sum:**

the md5sum hash value of the ota bin file



```
{
    "streamId": "TestStream55667788",
    "description": "This stream is used for sending 1 ota stream file to devices.",
    "files": [
        {
            "fileId": 69,
            "s3Location": {
                "bucket": "iot-ota-upgrade-package-bb",
                "key": "69/aws_demo.bin"
            }
        }
    ],
    "roleArn": "arn:aws:iam::482862934379:role/iotlabtpe-ota"
}

```

[**streamId**](https://docs.aws.amazon.com/iot/latest/apireference/API_CreateStream.html#API_CreateStream_RequestSyntax)

The stream ID.
Length Constraints: Minimum length of 1. Maximum length of 128.

[**description**](https://docs.aws.amazon.com/iot/latest/apireference/API_CreateStream.html#API_CreateStream_RequestSyntax)

A description of the stream.
Type: String
Length Constraints: Maximum length of 2028.

[**files**](https://docs.aws.amazon.com/iot/latest/apireference/API_CreateStream.html#API_CreateStream_RequestSyntax)

The files to stream.
Type: Array of [StreamFile](https://docs.aws.amazon.com/iot/latest/apireference/API_StreamFile.html) objects
Array Members: Minimum number of 1 item. Maximum number of 50 items.
Required: Yes

[**roleArn**](https://docs.aws.amazon.com/iot/latest/apireference/API_CreateStream.html#API_CreateStream_RequestSyntax)

An IAM role that allows the IoT service principal assumes to access your S3 files.
Type: String
Length Constraints: Minimum length of 20. Maximum length of 2048.
Required: Yes
stream document


### Running OtaStressStart.sh:

sh OtaStressStart.sh <ThingListFile> <JobID> <Rounds> <job.json> <create-stream.json> <StreamID>
**Description**:
OtaStressStart.sh parse the thingLists.txt and then starts the a deployment or repeated stress test. If you want to use your own job/stream documents, you can run OtaStressStart.sh without OtaEnvBuild.sh, and deploy jobs with your customized job/stream documents 

* ThingListFile:
    *  for example Thinglist.txt like the above example
* JobID:
    * input the job id you would like to use in the test, and you can track the status on IoT Console, the job will be deleted after the test is completed. 
    * The scripts will automatically create the job document and create the job, but you cab also follow [this documentation](https://docs.aws.amazon.com/cli/latest/reference/iot/create-job.html) to customize the job document information. 
* Rounds:
    * when you use this tool for deploying an OTA firmware update, set this value to 1. Use a value larger than 1 for repeated testing purpose. This tool will deploy the same OTA job repeatedly for $Rounds times; if failure happens, the deployment will stop and the rest of the $Rounds will be skipped.
* StreamID:
    * input the stream id you would like to use in the test. The stream will be deleted after the test is completed. 
    * The scripts will automatically create the stream document and create the stream, but you cab also follow [this documentation](https://docs.aws.amazon.com/cli/latest/reference/iot/create-stream.html) to customize the stream document information. 
* job.json
    * The job document you’ve customized in the above section. if you run main.sh, the document is created automatically 
* create-stream.json
    * The stream document you’ve customized in the above section. if you run main.sh, the document is created automatically 

```
sh OtaStressStart.sh ThingList.txt MyJobID123 2 file://example-job.json  file://create-stream.json MyStreamID123
```



# Deploy OTA firmware updates using python:

## Description:

In the first section we will go through how to setup a deployment or repeated stress test by using the shell scripts. Here we want to highlight some benefits using python scripts.
For example, you can customize more parameters:

1. The debug method to stdout or log file 
2. whether to clean up the results after testing
3. the region and bucket you would like to use for testing
4. the delay for each AWS IoT operations (creating jobs, deleting jobs)

We’ve also created a client monitor to polling the status and statistics for users to get more information of the jobs and each device status

## Prerequisites:

1. you need to have AWS account
2. Install [python3](https://realpython.com/installing-python/) 
3. Create IAM user maker sure it has [OTA required user policy](https://docs.aws.amazon.com/freertos/latest/userguide/create-ota-user-policy.html)
4. [Create an OTA update service role](https://docs.aws.amazon.com/freertos/latest/userguide/create-service-role.html)

### List down the devices that will be update through OTA 

There are many ways to filter out the target devices of interest. 

1. you can create a group of your devices by [AWS IoT Device Management](https://docs.aws.amazon.com/iot/latest/developerguide/thing-groups.html) and use [AWS CLI to describe the ARN of the group](https://docs.aws.amazon.com/cli/latest/reference/iot/describe-thing-group.html), then copy the ARN to thingList.txt
2. you can also [list down the devices one by one with AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/iot/describe-thing.html) and copy the ARN to thingList.txt


After listed down the devices, your thingList.txt file should look like this :

![](./docs/thinglist.png)

## Running jobs.py

**Description:**

jobs.py creates the job,stream documents, upload the bin file to S3, parse the thingLists.txt and then starts a deployment or repeated stress test. with the parameters set in dev.ini

### Usage:

update the **dev.ini in src** folder

![](./docs/src_folder.png)

```
[DEFAULT]
thingList = thingsList.txt
binName = test.bin
roleArn = arn:aws:iam::12345678:role/<your_role>
jobId = <yourJobId>
rounds = 34
bucket = iot-ota-deployment-tool
cleanUpCfg = True
debug = False
default_delay = 5
region = us-east-1
streamId = <yourSteamId>
iot_api_sleep_time = 15
file_chunck_size = 8192

```

* thingList:
    *  for example Thinglist.txt like the above example
* binName:  
    * the binary that you wish to update, it will be uploaded to S3 by the script durring the test
* roleArn: 
    * the ota role you’ve created, it should look like “**arn:aws:iam::123456789:role/your_ota_role**“ and given [OTA update service role](https://docs.aws.amazon.com/freertos/latest/userguide/create-service-role.html) access
* jobId:
    * input the job id you would like to use in the test, and you can track the status on IoT Console, the job will be deleted after the test is completed. See [this documentation](https://github.com/awsblake/aws-iot-device-sdk-embedded-C/blob/dla_review/README.md) for how to create such a job.  See this section of this doc if you want to use a script to create the job for you. 
* rounds:
    * when you use this tool for deploying an OTA firmware update, set this value to 1. Use a value larger than 1 for repeated testing purpose. This tool will deploy the same OTA job repeatedly for $rounds times; if failure happens, the deployment will stop and the rest of the $rounds will be skipped.
* streamId:
    * input the stream id you would like to use in the test. The stream will be deleted after the test is completed. The python scripts will automatically create the stream document and create the stream, but you cab also follow [this documentation](https://docs.aws.amazon.com/cli/latest/reference/iot/create-stream.html) to customize the stream information. 
* bucket:
    * the bucket which is used for OTA Jobs, it will be use to upload bin file and json documents
* cleanUpCfg:
    * to decide if the jobs will be clean up after the test is done
* debug:
    * to decide if the log output will be write to a file or output to stdout
* default_delay:
    * the delay time for each round
* region:
    * the region that will be used in this test
* iot_api_sleep_time:
    * the delay time for each time calling AWS IoT api
* file_chunck_size:
    * To calculate md5 sum of the file, the file will be divided into chunks and calculate the hash value and combine the results as the file’s md5 sum value, if the file can not be divide by the chunk size, the remainder will be hashed alone.

### 

### **Start deploy jobs for test:**

```
python3 jobs.py
```



## Running monitor.py

**Description:**

monitor.py monitors the status of the jobs and also checks mqtt messages status while the jobs is ongoing to give the users an idea if the devices are executing OTA, if it encountered some issue. it’s a tool aside from jobs.py

### Usage:

monitor.py takes the same **dev.ini** file as parameters 


```
python3 monitor.py
```
