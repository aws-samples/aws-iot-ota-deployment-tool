import boto3
import time
import logging
import sys
import configparser
import os.path as path

from aws_interfaces.iot_interface import IotInterface


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# Initializing parameters:
config = configparser.ConfigParser()
config.read('dev.ini')
if 'DEFAULT' not in config:
    raise Exception('invalid config')

jobId = config['DEFAULT']['jobId']
debug = config['DEFAULT'].getboolean('debug')
defaultDelay = int(config['DEFAULT']['defaultDelay'])
region = config['DEFAULT']['region']
thingListFilePath = config['DEFAULT']['thingList']
cloudwatch = boto3.client('logs', region_name=region)


def parse_thingList(thingListFilePath):
    logging.info("parse_thingList.....")
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


class monitor_tool():
    def __init__(self):
        thingArnList, deviceCount, thingNameList = parse_thingList(thingListFilePath)
        if deviceCount < 1:
            raise Exception('thing list should not be empty')
        self.thingArnList = thingArnList
        self.deviceCount = deviceCount
        self.thingNameList = thingNameList
        self.thingListUpdateTime = 0
        self.iot_interface = IotInterface(region)

    def monitor_start(self):
        isParseList = False
        job_complete_counter = 0
        while True:
            fileUpdateTime = path.getmtime(thingListFilePath)
            if fileUpdateTime > self.thingListUpdateTime or isParseList is True:
                thingArnList, deviceCount, thingNameList = parse_thingList(thingListFilePath)
                self.thingListUpdateTime = path.getmtime(thingListFilePath)
                isParseList = False

            if len(thingArnList) < 1 or deviceCount < 1:
                raise Exception('thing list should not be empty')
            if deviceCount > self.deviceCount:
                self.thingArnList = thingArnList
                self.deviceCount = deviceCount
                self.thingNameList = thingNameList
            job_dsb, err = self.iot_interface.get_job_info(jobId)
            if job_dsb:
                status = job_dsb.get('status')
            else:
                continue
            if err:
                logging.error(err)
                return
            if status == 'COMPLETED':
                isParseList = True
                numberOfSucceededThings = job_dsb.get('jobProcessDetails', {}).get('numberOfSucceededThings')
                if numberOfSucceededThings >= self.deviceCount:
                    job_complete_counter = job_complete_counter + 1
                    logging.info('deviceCount: %d matches numberOfSucceededThings: %d job completed with success', self.deviceCount, numberOfSucceededThings)
                    logging.info('jobId : %s  completed , job_complete_counter: %d', jobId, job_complete_counter)
                    logging.info('jobId %s completed', jobId)
                else:
                    logging.info('deviceCount: %d does not matches numberOfSucceededThings: %d job completed with failure', self.deviceCount, numberOfSucceededThings)
                    break
            elif status == 'IN_PROGRESS':
                logging.info('jobId %s IN_PROGRESS', jobId)
                thingNameList = self.thingNameList
                for thingName in thingNameList:
                    job_exe_dsb, err = self.iot_interface.get_job_exe_info(jobId, thingName)
                    if job_exe_dsb:
                        thing_status = job_exe_dsb.get('status')
                        if thing_status == 'SUCCEEDED':
                            self.thingNameList.remove(thingName)
                        else:
                            logging.info('thing name: %s status: %s statusDetails %s: ', thingName, thing_status, job_exe_dsb['statusDetails'])

            elif status == 'CANCELED' or status == 'DELETION_IN_PROGRESS' or status == 'DELETION_IN_PROGRESS':
                logging.info('unexpected failure with status: %s', status)
                isParseList = True
            else:
                logging.info('unexpected status: %s', status)
                break
            time.sleep(defaultDelay)


def main():
    monitor = monitor_tool()
    monitor.monitor_start()

if __name__ == '__main__':
    main()
