import json
import boto3
import time
import logging
import sys
import configparser
import logging
from botocore.exceptions import ClientError


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class IotInterface:
    def __init__(self, region):
        self.client = boto3.client('iot', region_name=region)

    def create_stream(self, streamId, fileId, bucket, key, role_arn):
        logging.info('create_stream streamId %s with fileId %s', streamId, fileId)
        try:
            response = self.client.create_stream(
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

    def create_job(self, deployConfig):
        logging.info('create_job jobId %s', deployConfig['defaultConfig']['jobId'])
        kwargs = {
            'jobId': deployConfig['defaultConfig']['jobId'],
            'targets': deployConfig['defaultConfig']['thingArnList'],
            'documentSource': deployConfig['defaultConfig']['jobDocumentSrc'],
            'targetSelection': deployConfig['defaultConfig']['targetSelection']
        }

        if 'presignedUrlConfig' in deployConfig:
            kwargs['presignedUrlConfig'] = deployConfig['presignedUrlConfig']
        if 'jobExecutionsRolloutConfig' in deployConfig:
            kwargs['jobExecutionsRolloutConfig'] = deployConfig['jobExecutionsRolloutConfig']
        if 'abortConfig' in deployConfig:
            kwargs['abortConfig'] = deployConfig['abortConfig']
        if 'timeoutConfig' in deployConfig:
            kwargs['timeoutConfig'] = deployConfig['timeoutConfig']

        try:
            response = self.client.create_job(**kwargs)
        except ClientError as e:
            return False, str(e)
        return True, None

    def get_job_info(self, jobId):
        logging.info('get_job_info for jobId %s', jobId)
        job_dsb = None
        try:
            response = self.client.describe_job(jobId=jobId)
            job_dsb = response.get('job')
        except ClientError as e:
            return None, str(e)
        return job_dsb, None

    def get_job_exe_info(self, jobId, thingName):
        logging.info('get_job_exe_info for jobId %s, thingName: %s', jobId, thingName)
        job_exe_dsb = None
        try:
            response = self.client.describe_job_execution(jobId=jobId, thingName=thingName)
            job_exe_dsb = response.get('execution')
        except ClientError as e:
            return None, str(e)
        return job_exe_dsb, None

    def cancel_job(self, jobId):
        logging.info('canceling jobId %s', jobId)
        try:
            self.client.cancel_job(jobId=jobId)
        except ClientError as e:
            return False, str(e)
        while True:
            try:
                response = self.client.describe_job(jobId=jobId)
                job_dsb = response.get('job')
                status = job_dsb.get('status')
                if status == 'CANCELED':
                    break
                time.sleep(1)
            except ClientError as e:
                break
        return True, None

    def delete_job(self, jobId):
        logging.info('deleting jobId %s', jobId)
        try:
            self.client.delete_job(jobId=jobId, force=True)
        except ClientError as e:
            return False, str(e)
        while True:
            try:
                response = self.client.describe_job(jobId=jobId)
                time.sleep(1)
            except ClientError as e:
                break
        return True, None

    def delete_stream(self, streamId):
        logging.info('deleting streamId %s', streamId)
        try:
            self.client.delete_stream(streamId=streamId)
        except ClientError as e:
            return False, str(e)
        while True:
            try:
                response = self.client.describe_stream(streamId=streamId)
                time.sleep(1)
            except ClientError as e:
                break
        return True, None
