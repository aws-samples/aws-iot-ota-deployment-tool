import time
import jobs_configure
import logging
import sys
import configparser

from aws_interfaces.iot_interface import IotInterface
from aws_interfaces.alarm_interface import AlarmInterface

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class ota_deployment_tool():
    def __init__(self, config):
        deployConfig = jobs_configure.init_config(config)
        self.deployConfig = deployConfig
        self.alarm_interface = AlarmInterface(deployConfig['defaultConfig']['region'])
        self.iot_interface = IotInterface(deployConfig['defaultConfig']['region'])
        self.clean_up(deployConfig)

    def clean_up(self, deployConfig):
        cleanUpCfg = deployConfig['defaultConfig']['cleanUpCfg']
        streamId = deployConfig['defaultConfig']['streamId']
        jobId = deployConfig['defaultConfig']['jobId']
        if cleanUpCfg:
            logging.info('deleting old job')
            self.iot_interface.delete_job(jobId)
            logging.info('deleting old stream')
            self.iot_interface.delete_stream(streamId)
            logging.info('deleting old alarms')
            if 'alarmConfigs' in deployConfig:
                self.alarm_interface.delete_alarms(deployConfig['alarmConfigs'])
        else:
            logging.info('skipping clean_up due to cleanUpCfg set to false')

    def schedule_jobs(self, deployConfig):
        logging.info('creating new stream')
        streamId = deployConfig['defaultConfig']['streamId']
        fileId = deployConfig['defaultConfig']['fileId']
        bucket = deployConfig['defaultConfig']['bucket']
        binFileKey = deployConfig['defaultConfig']['binFileKey']
        roleArn = deployConfig['defaultConfig']['roleArn']
        jobId = deployConfig['defaultConfig']['jobId']
        thingArnList = deployConfig['defaultConfig']['thingArnList']
        jobDocumentSrc = deployConfig['defaultConfig']['jobDocumentSrc']
        deviceCount = deployConfig['defaultConfig']['deviceCount']
        defaultDelay = deployConfig['defaultConfig']['defaultDelay']
        rounds = deployConfig['defaultConfig']['rounds']

        if 'alarmConfigs' in deployConfig:
            status, err = self.alarm_interface.create_alarms(deployConfig['alarmConfigs'])
            if not status:
                logging.error(err)
                return

        status, err = self.iot_interface.create_stream(streamId, fileId, bucket, binFileKey, roleArn)
        if not status:
            logging.error(err)
            return
        status, err = self.iot_interface.create_job(deployConfig)
        if not status:
            logging.error(err)
            return
        job_complete_counter = 0
        while job_complete_counter < rounds:
            job_dsb, err = self.iot_interface.get_job_info(jobId)
            status = job_dsb.get('status')
            if err:
                logging.error(err)
                return
            if status == 'COMPLETED':
                numberOfSucceededThings = job_dsb.get('jobProcessDetails', {}).get('numberOfSucceededThings')
                if numberOfSucceededThings == deviceCount:
                    job_complete_counter = job_complete_counter + 1
                    logging.info('deviceCount: %d matches numberOfSucceededThings: %d job completed with success',
                                 deviceCount, numberOfSucceededThings)
                    logging.info('jobId : %s  completed , job_complete_counter: %d', jobId, job_complete_counter)
                    logging.info('jobId %s completed', jobId)
                    self.clean_up(deployConfig)
                    if job_complete_counter < rounds:
                        logging.info('creating new stream')
                        status, err = self.iot_interface.create_stream(streamId, fileId, bucket, binFileKey, roleArn)
                        if not status:
                            logging.error(err)
                            return
                        logging.info('creating new job, thingArnList: %s', thingArnList)
                        status, err = self.iot_interface.create_job(jobId, thingArnList, jobDocumentSrc)
                        if not status:
                            logging.error(err)
                            return
                else:
                    logging.info('deviceCount: %d does not matches numberOfSucceededThings: %d job completed with failure',
                                 deviceCount, numberOfSucceededThings)
                    break
            elif status == 'IN_PROGRESS':
                logging.info('jobId: %s  IN_PROGRESS: ', jobId)
            elif status == 'CANCELED' or status == 'DELETION_IN_PROGRESS' or status == 'DELETION_IN_PROGRESS':
                logging.info('unexpected failure with status: %s', status)
                break
            else:
                logging.info('unexpected status: %s', status)
                break
            time.sleep(defaultDelay)


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
