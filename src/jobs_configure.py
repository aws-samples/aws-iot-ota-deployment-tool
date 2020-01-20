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
configMap = {
    'PRESIGNED_URL_CONFIG' : 'usePresignedUrlConfig',
    'CUSTOM_JOB_DOCUMENT' : 'useCustomJobDocument',
    'JOB_EXECUTE_ROLLOUT_CONFIG' : 'useJobExecutionsRolloutConfig',
    'ABORT_CONFIG' : 'useAbortConfig',
    'TIMEOUT_CONFIG' : 'useTimeoutConfig',
    'EXP_RATE_CONFIG': 'useExponentialRateCfg',
    'INCREASE_CRITERIA': 'useRateIncreaseCriteria',
    'ABORT_CONFIG_TYPE_ALL': 'useAllSubsection',
    'ABORT_CONFIG_TYPE_FAILED': 'useFailedSubsection',
    'ABORT_CONFIG_TYPE_REJECTED': 'useRejectedSubsection',
    'ABORT_CONFIG_TYPE_TIMED_OUT': 'useTimedOutSubsection'
}

def is_config_in_use(config, sectionName, checkInSection):
    checkConfig = configMap[sectionName]
    useConfig = config[checkInSection].getboolean(checkConfig)
    if useConfig:
        if sectionName not in config:
            raise Exception('invalid config. %s set True, requires %s section', checkConfig, sectionName)
        else:
            status = True
    else:
        status = False
    return status

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

def md5_check_sum(filePath, fileChunkSize):
    logging.info( "md5_check_sum.....")
    with open(filePath, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(fileChunkSize)
            if not data:
                break
            m.update(data)
        logging.info(m.hexdigest())
        return m.hexdigest()

def create_job_document(jobDocConfig):
    md5sum = jobDocConfig['md5sum']
    fileSize = jobDocConfig['fileSize']
    fileId = jobDocConfig['fileId']
    bucket = jobDocConfig['bucket']
    streamId = jobDocConfig['streamId']

    if 'jobDocPath' in jobDocConfig:
        jobDocPath = jobDocConfig['jobDocPath']
        logging.info("updating job json file %s", jobDocPath)
        with open(jobDocPath, 'rb') as jobDoc:
            data = json.load(jobDoc)
    else:
        logging.info("creating job json")
        data = {}

    data['command'] = 'fota'
    data['streamId'] = streamId
    data['fileId'] = fileId
    data['fileSize'] = fileSize
    data['md5sum'] = md5sum

    with open('job.json', 'w') as outfile:
        json.dump(data, outfile)
        key='job' + str(fileId) + '.json'
    status = upload_file_to_s3('job.json', bucket, key)
    jobDocumentSrc = 'https://{}.s3.amazonaws.com/job{}.json'.format(bucket, str(fileId))
    return status, jobDocumentSrc

def job_doc_section_parser(config, defaultConfig):
    jobDocConfig = {
        'md5sum': defaultConfig['md5sum'],
        'fileSize': defaultConfig['fileSize'],
        'fileId': defaultConfig['fileId'],
        'bucket': defaultConfig['bucket'],
        'streamId': defaultConfig['streamId']
    }
    status = is_config_in_use(config, 'CUSTOM_JOB_DOCUMENT', 'DEFAULT')
    if status:
        jobDocConfig['jobDocPath'] = config['CUSTOM_JOB_DOCUMENT']['jobDocPath']
    status, jobDocumentSrc = create_job_document(jobDocConfig)
    if status:
        return jobDocumentSrc
    else:
        raise Exception('create_job_document failed')

def presigned_url_section_parser(config):
    presignedUrlConfig = {}
    status = is_config_in_use(config, 'PRESIGNED_URL_CONFIG', 'DEFAULT')
    if status:
        presignedUrlConfig['roleArn'] = config['PRESIGNED_URL_CONFIG']['roleArn']
        presignedUrlConfig['expiresInSec'] = int(config['PRESIGNED_URL_CONFIG']['expiresInSec'])
    return status, presignedUrlConfig

def job_exec_rollout_cfg_section_parser(config):
    JobExecutionsRolloutConfig = {}
    status = is_config_in_use(config, 'JOB_EXECUTE_ROLLOUT_CONFIG', 'DEFAULT')
    if status:
        JobExecutionsRolloutConfig['maximumPerMinute'] = int(config['JOB_EXECUTE_ROLLOUT_CONFIG']['maximumPerMinute'])
        if is_config_in_use(config, 'EXP_RATE_CONFIG', 'JOB_EXECUTE_ROLLOUT_CONFIG'):
            JobExecutionsRolloutConfig['exponentialRate'] = {
                'baseRatePerMinute': int(config['EXP_RATE_CONFIG']['baseRatePerMinute']),
                'incrementFactor': float(config['EXP_RATE_CONFIG']['incrementFactor'])
            }
            if is_config_in_use(config, 'INCREASE_CRITERIA', 'EXP_RATE_CONFIG'):
                JobExecutionsRolloutConfig['exponentialRate']['rateIncreaseCriteria'] = {
                    'numberOfNotifiedThings': int(config['INCREASE_CRITERIA']['numberOfNotifiedThings']),
                    'numberOfSucceededThings': int(config['INCREASE_CRITERIA']['numberOfSucceededThings'])
                }


    return status, JobExecutionsRolloutConfig

def abort_cfg_section_parser(config):
    abortConfig = {}
    status = is_config_in_use(config, 'ABORT_CONFIG', 'DEFAULT')
    if status:
        failureTypeList = ['ALL', 'FAILED', 'REJECTED', 'TIMED_OUT']
        abortConfig['criteriaList'] = []
        for failureType in failureTypeList:
            failureTypeConfig = 'ABORT_CONFIG_TYPE_' + failureType
            if is_config_in_use(config, failureTypeConfig, 'ABORT_CONFIG'):
                abortConfig['criteriaList'].append( {
                    'failureType': failureType,
                    'action': 'CANCEL',
                    'thresholdPercentage': float(config[failureTypeConfig]['thresholdPercentage']),
                    'minNumberOfExecutedThings': int(config[failureTypeConfig]['minNumberOfExecutedThings'])
                })
                if failureType == 'ALL':
                    break
    return status, abortConfig

def timeout_cfg_section_parser(config):
    timeoutConfig = {}
    status = is_config_in_use(config, 'TIMEOUT_CONFIG', 'DEFAULT')
    if status:
        timeoutConfig['inProgressTimeoutInMinutes'] = int(config['TIMEOUT_CONFIG']['inProgressTimeoutInMinutes'])
    return status, timeoutConfig

def default_section_parser(config):
    defaultConfig = {
        'thingListFilePath': config['DEFAULT']['thingList'],
        'binName': config['DEFAULT']['binName'],
        'roleArn': config['DEFAULT']['roleArn'],
        'jobId': config['DEFAULT']['jobId'],
        'rounds': int(config['DEFAULT']['rounds']),
        'bucket': config['DEFAULT']['bucket'],
        'cleanUpCfg': config['DEFAULT'].getboolean('cleanUpCfg'),
        'debug': config['DEFAULT'].getboolean('debug'),
        'defaultDelay': int(config['DEFAULT']['defaultDelay']),
        'useCustomJobDocument': config['DEFAULT'].getboolean('useCustomJobDocument'),
        'region':  config['DEFAULT']['region'],
        'fileChunkSize': int(config['DEFAULT']['fileChunkSize']),
        'targetSelection': config['DEFAULT']['targetSelection']
    }
    binName = defaultConfig['binName']
    fileChunkSize = defaultConfig['fileChunkSize']
    thingListFilePath = defaultConfig['thingListFilePath']
    fileChunkSize = defaultConfig['fileChunkSize']
    bucket = defaultConfig['bucket']

    seed(1)
    fileId = randint(1, 255)
    defaultConfig['streamId'] = config['DEFAULT']['streamId'] + '_' + str(fileId)
    defaultConfig['binFileKey'] = 'firmware/' + time.strftime("%Y%m%d-%H%M%S") + binName
    binFileKey = defaultConfig['binFileKey']
    status = False
    file_stats = os.stat(binName)
    defaultConfig['md5sum'] = md5_check_sum(binName, fileChunkSize)
    thingArnList, deviceCount, thingNameList = parse_thingList(thingListFilePath)
    if deviceCount < 1:
        raise Exception('thing list should not be empty')
    status = upload_file_to_s3(binName, bucket, binFileKey)
    if status == False:
        raise Exception('job configure upload binFile failed')
    defaultConfig['thingArnList'] = thingArnList
    defaultConfig['thingNameList'] = thingNameList
    defaultConfig['deviceCount'] = deviceCount
    defaultConfig['fileId'] = fileId
    defaultConfig['fileSize'] = file_stats.st_size
    return defaultConfig

def init_config(config):
    deployConfig = {}
    defaultConfig = default_section_parser(config)
    jobDocumentSrc = job_doc_section_parser(config, defaultConfig)
    defaultConfig['jobDocumentSrc'] = jobDocumentSrc
    deployConfig['defaultConfig'] = defaultConfig
    status, presignedUrlConfig = presigned_url_section_parser(config)
    if status:
        deployConfig['presignedUrlConfig'] = presignedUrlConfig
    else:
        deployConfig['presignedUrlConfig'] = None

    status, jobExecutionsRolloutConfig = job_exec_rollout_cfg_section_parser(config)
    if status:
        deployConfig['jobExecutionsRolloutConfig'] = jobExecutionsRolloutConfig
    else:
        deployConfig['jobExecutionsRolloutConfig'] = None
    status, abortConfig = abort_cfg_section_parser(config)
    if status:
        deployConfig['abortConfig'] = abortConfig
    else:
        deployConfig['abortConfig'] = None
    status, timeoutConfig = timeout_cfg_section_parser(config)
    if status:
        deployConfig['timeoutConfig'] = timeoutConfig
    else:
        deployConfig['timeoutConfig'] = None

    return deployConfig


if __name__ == '__main__':
    main()
