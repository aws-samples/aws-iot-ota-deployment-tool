import json
import boto3
import time
import logging
import sys
import configparser
import logging
from botocore.exceptions import ClientError


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# Initializing parameters:
config = configparser.ConfigParser()
config.read('dev.ini')
if 'DEFAULT' not in config:
    raise Exception('invalid config')
thingList =  config['DEFAULT']['thingList']
iot_api_sleep_time = int(config['DEFAULT']['iot_api_sleep_time'])
region = config['DEFAULT']['region']

iot = boto3.client('iot', region_name=region)

def create_stream(streamId, fileId, bucket, key, role_arn):
    logging.info('create_stream streamId %s with fileId %s', streamId, fileId)
    try:
        response = iot.create_stream(
            streamId=streamId,
            description='testing',
            files=[
                {
                    "fileId": fileId,
                    "s3Location": {
                        "bucket": bucket,
                        "key": key
                    }
                }
            ],
            roleArn=role_arn
        )
    except ClientError as e:
        return False, str(e)
    return True, None

def create_job(jobId, thingArn, documentSource):
    logging.info('create_job jobId %s', jobId)
    try:
        response = iot.create_job(
            jobId=jobId,
            targets=thingArn,
            documentSource=documentSource,
            description='testingJob',
            targetSelection='SNAPSHOT'
        )
    except ClientError as e:
        return False, str(e)
    return True, None

def get_job_info(jobId):
    logging.info('get_job_info for jobId %s', jobId )
    try:
        response = iot.describe_job(jobId=jobId)
        job_dsb = response.get('job')
    except ClientError as e:
        return None, str(e)
    return job_dsb, None

def get_job_exe_info(jobId, thingName):
    logging.info('get_job_exe_info for jobId %s, thingName: %s', jobId, thingName)
    try:
        response = iot.describe_job_execution(jobId=jobId, thingName=thingName)
        job_exe_dsb = response.get('execution')
    except ClientError as e:
        return None, str(e)
    return job_exe_dsb, None


def cancel_job(jobId):
    logging.info('canceling jobId %s', jobId)
    try:
        iot.cancel_job(jobId=jobId)
    except ClientError as e:
        return False, str(e)
    time.sleep(iot_api_sleep_time)
    return True, None


def delete_job(jobId):
    logging.info('deleting jobId %s', jobId)
    try:
        iot.delete_job(jobId=jobId, force=True)
    except ClientError as e:
        return False, str(e)
    time.sleep(iot_api_sleep_time)
    return True, None

def delete_stream(streamId):
    logging.info('deleting streamId %s', streamId)
    try:
        iot.delete_stream(streamId=streamId)
    except ClientError as e:
        return False, str(e)
    time.sleep(iot_api_sleep_time)
    return True, None

