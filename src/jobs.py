import os
import json
import boto3
import time
import hashlib
import iot_interface
import jobs_configure
import logging
import sys
import configparser
from random import seed
from random import randint
from botocore.exceptions import ClientError


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class ota_deployment_tool():
    def __init__(self, config):
        deployConfig = jobs_configure.init_config(config)
        self.deployConfig = deployConfig
        self.clean_up(deployConfig)

    def clean_up(self, deployConfig):
        cleanUpCfg = deployConfig.get('cleanUpCfg')
        streamId = deployConfig.get('streamId')
        jobId = deployConfig.get('jobId')
        if cleanUpCfg:
            logging.info('deleting old job')
            iot_interface.delete_job(jobId)
            logging.info('deleting old stream')
            iot_interface.delete_stream(streamId)
        else:
            logging.info('skipping clean_up due to cleanUpCfg set to false')

    def schedule_jobs(self, deployConfig):
        logging.info('creating new stream')
        streamId = deployConfig['streamId']
        fileId = deployConfig['fileId']
        bucket = deployConfig['bucket']
        binFileKey = deployConfig['binFileKey']
        roleArn = deployConfig['roleArn']
        jobId = deployConfig['jobId']
        thingArnList = deployConfig['thingArnList']
        jobDocumentSrc = deployConfig['jobDocumentSrc']
        deviceCount = deployConfig['deviceCount']
        default_delay = deployConfig['default_delay']
        rounds = deployConfig['rounds']
        status , err = iot_interface.create_stream(streamId, fileId, bucket, binFileKey ,roleArn)
        if status == False:
            logging.error(err)
            return
        status , err = iot_interface.create_job(jobId, thingArnList, jobDocumentSrc)
        if status == False:
            logging.error(err)
            return
        job_complete_counter = 0
        while job_complete_counter < rounds:
            job_dsb, err = iot_interface.get_job_info(jobId)
            status = job_dsb.get('status')
            if err:
                logging.error(err)
                return
            if status == 'COMPLETED':
                numberOfSucceededThings = job_dsb.get('jobProcessDetails', {}).get('numberOfSucceededThings')
                if numberOfSucceededThings == deviceCount:
                    job_complete_counter = job_complete_counter + 1
                    logging.info('deviceCount: %d matches numberOfSucceededThings: %d job completed with success', deviceCount, numberOfSucceededThings)
                    logging.info('jobId : %s  completed , job_complete_counter: %d',jobId, job_complete_counter)
                    logging.info('jobId %s completed', jobId )
                    self.clean_up(deployConfig)
                    if job_complete_counter < rounds:
                        logging.info('creating new stream')
                        status , err = iot_interface.create_stream(streamId, fileId, bucket, binFileKey ,roleArn)
                        if status == False:
                            logging.error(err)
                            return
                        logging.info('creating new job, thingArnList: %s', thingArnList)
                        status , err = iot_interface.create_job(jobId, thingArnList , jobDocumentSrc)
                        if status == False:
                            logging.error(err)
                            return
                else:
                    logging.info('deviceCount: %d does not matches numberOfSucceededThings: %d job completed with failure', deviceCount, numberOfSucceededThings)
                    break;
            elif status == 'IN_PROGRESS':
                logging.info('jobId: %s  IN_PROGRESS: ', jobId)
            elif status == 'CANCELED' or status == 'DELETION_IN_PROGRESS' or status == 'DELETION_IN_PROGRESS':
                logging.info('unexpected failure with status: %s', status)
                break;
            else:
                logging.info('unexpected status: %s', status)
                break;
            time.sleep( default_delay )

def main():
    config = configparser.ConfigParser()
    config.read('dev.ini')
    if 'DEFAULT' not in config:
        raise Exception('invalid config')
    ota_jobs = ota_deployment_tool(config)
    ota_jobs.schedule_jobs(ota_jobs.deployConfig)
    ota_jobs.clean_up(ota_jobs.deployConfig)


if __name__ == '__main__':
    main()
