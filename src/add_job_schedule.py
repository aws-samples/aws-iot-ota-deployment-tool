import boto3
import os
import string
import random
import time
import argparse
import logging
import sys
import configparser
import json
import datetime
from botocore.exceptions import ClientError
from aws_interfaces.s3_interface import S3Interface

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--method", action="store", required=True, dest="method", help="submit or create")
parser.add_argument("-f", "--binFile", action="store", required=True, dest="binName", help="the file that you wish to update through OTA")
parser.add_argument("-tb", "--tableName", action="store", required=True, dest="tableName", help="the table for jobs entry")
parser.add_argument("-b", "--bucket", action="store", required=True, dest="bucket", help="bucket name")
parser.add_argument("-r", "--region", action="store", required=True, dest="region", help="the region for uploading")
parser.add_argument("-d", "--devIni", action="store", required=False, dest="devIniFile", default="None", help="customized streamId")
parser.add_argument("-l", "--thingList", action="store", required=False, dest="thingListFile", default="None", help="customized streamId")

config = configparser.ConfigParser()
config.optionxform = lambda option: option
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
args = parser.parse_args()
region = args.region
binFileName = args.binName
tableName = args.tableName
method = args.method
bucket = args.bucket
thingListFile = args.thingListFile
devIniFile = args.devIniFile
dynamodb = boto3.client('dynamodb', region_name=region)
s3_interface = S3Interface(region)


def create_new_job_config():
    # user can update a new job config throug hci
    return True


def is_submit_param_valid(binFileName, thingListFile, devIniFile):
    status = True
    if not os.path.isfile(binFileName):
        status = False
        print(binFileName, 'failed')
    if not os.path.isfile(thingListFile):
        status = False
        print(thingListFile, 'failed')
    if not os.path.isfile(devIniFile):
        status = False
        print(devIniFile, 'failed')

    config.read(devIniFile)
    if config['DEFAULT']['binName'] != binFileName:
        status = False
        print('binFileName not matched')
    if config['DEFAULT']['thingList'] != thingListFile:
        status = False
        print('thingListFile not matched')
    return status


def submit_job_config():
    if is_submit_param_valid(binFileName, thingListFile, devIniFile):
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        config.read(devIniFile)
        jobId = 'jobId_' + timestamp
        streamId = 'streamId_' + timestamp
        binName = 'binFile_' + jobId + '_' + binFileName
        binFileKey = 'release/' + binName
        devFileName = 'devFile_' + jobId + '_' + devIniFile
        devFileKey = 'release/' + devFileName
        thingListFileName = 'thingListFile_' + jobId + '_' + thingListFile
        thingListFileKey = 'release/' + thingListFileName
        config['DEFAULT']['thingList'] = thingListFileName
        config['DEFAULT']['jobId'] = jobId
        config['DEFAULT']['streamId'] = streamId
        config['DEFAULT']['binName'] = binName
        with open(devFileName, 'w') as configfile:
            config.write(configfile)

        s3_interface.upload_file_to_s3(devFileName, bucket, devFileKey)
        s3_interface.upload_file_to_s3(binFileName, bucket, binFileKey)
        s3_interface.upload_file_to_s3(thingListFile, bucket, thingListFileKey)
        jobStatus = 'PendingDeployment'
        dynamodb.put_item(
            TableName=tableName,
            Item={
                'jobId': {'S': jobId},
                'bucketId': {'S': bucket},
                'binFileKey': {'S': binFileKey},
                'thingListFileKey': {'S': thingListFileKey},
                'devFileKey': {'S': devFileKey},
                'jobStatus': {'S': jobStatus},
                'timestamp': {'S': timestamp}
            })
    else:
        raise Exception('submit config and param sanity check failed')


def add_job_entry():
    if method == 'submit':
        submit_job_config()
    elif method == 'create':
        create_new_job_config()
    else:
        raise Exception('unexpected input method, use submit or create')

add_job_entry()
