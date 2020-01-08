import os
import json
import boto3
import time
import hashlib
import iot_interface
import logging
import sys
import configparser
from random import seed
from random import randint
from botocore.exceptions import ClientError


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# Initializing parameters:
config = configparser.ConfigParser()
config.read('dev.ini')
if 'DEFAULT' not in config:
    raise Exception('invalid config')
region = config['DEFAULT']['region']

s3 = boto3.client('s3', region_name=region)


def upload_file_to_s3(fileName, bucket, key):
    logging.info( "upload file %s to bucket: %s", fileName, bucket)
    try:
        with open(fileName, 'rb') as objectData:
            s3.put_object(Body=objectData, Bucket=bucket, Key=key)
    except ClientError as e:
        logging.warn(str(e))
        return False
    return True

def parse_thingList(thingListFilePath):
    logging.info( "parse_thingList..... with path %s", thingListFilePath)
    thingArnList = []
    thingNameList = []
    deviceCount = 0
    filepath = thingListFilePath
    with open(filepath) as fp:
        for line in fp:
            if len(line) > 1:
                thingArn = line.strip()
                temp, thingName = thingArn.split(':thing/')
                thingArnList.append(str(thingArn))
                thingNameList.append(thingName)
                deviceCount += 1

    logging.info(thingArnList)
    return thingArnList, deviceCount, thingNameList

def md5Checksum(filePath, file_chunck_size):
    logging.info( "md5Checksum.....")
    with open(filePath, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(file_chunck_size)
            if not data:
                break
            m.update(data)
        logging.info(m.hexdigest())
        return m.hexdigest()

def create_job_document(md5sum, fileSize, fileId, bucket, streamId):
    logging.info("generating job json file")
    data = {
        "command": "fota",
        "streamId": streamId,
        "fileId": fileId,
        "fileSize": fileSize,
        "md5sum": md5sum
    }

    with open('job.json', 'w') as outfile:
        json.dump(data, outfile)
        key='job' + str(fileId) + '.json'
    status = upload_file_to_s3('job.json', bucket, key)
    job_doc_resource = 'https://{}.s3.amazonaws.com/job{}.json'.format(bucket, str(fileId))
    return status, job_doc_resource

def init_config(config):
    thingListFilePath =  config['DEFAULT']['thingList']
    binName = config['DEFAULT']['binName']
    roleArn = config['DEFAULT']['roleArn']
    jobId = config['DEFAULT']['jobId']
    rounds = int(config['DEFAULT']['rounds'])
    bucket = config['DEFAULT']['bucket']
    cleanUpCfg = config['DEFAULT'].getboolean('cleanUpCfg')
    debug = config['DEFAULT'].getboolean('debug')
    default_delay = int(config['DEFAULT']['default_delay'])
    region = config['DEFAULT']['region']
    file_chunck_size = int(config['DEFAULT']['file_chunck_size'])
    seed(1)
    fileId = randint(1, 255)
    streamId = config['DEFAULT']['streamId'] + '_' + str(fileId)
    binFileKey = 'firmware/' + time.strftime("%Y%m%d-%H%M%S") + binName
    config['DEFAULT']['streamId'] = streamId
    status = False
    file_stats = os.stat(binName)
    md5sum = md5Checksum(binName, file_chunck_size)
    thingArnList, deviceCount, thingNameList = parse_thingList(thingListFilePath)
    if deviceCount < 1:
        raise Exception('thing list should not be empty')
    status = upload_file_to_s3(binName, bucket, binFileKey)
    if status == False:
        raise Exception('job configure upload binFile failed')
    status, jobDocumentSrc = create_job_document(md5sum, file_stats.st_size, fileId, bucket, streamId)
    deployConfig = {
        "rounds": rounds,
        "roleArn": roleArn,
        "thingArnList": thingArnList,
        "deviceCount": deviceCount,
        "thingNameList": thingNameList,
        "jobDocumentSrc": jobDocumentSrc,
        "jobId": jobId,
        "bucket": bucket,
        "cleanUpCfg": cleanUpCfg,
        "debug": debug,
        "default_delay": default_delay,
        "streamId": streamId,
        "binFileKey": binFileKey,
        "fileId": fileId
    }
    return deployConfig


if __name__ == '__main__':
    main()
