import json
import boto3
import time
import logging
import sys
import logging
import os
from botocore.exceptions import ClientError


logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class S3Interface:
    def __init__(self, region):
        self.client = boto3.client('s3', region_name=region)

    def upload_file_to_s3(self, fileName, bucket, key):
        logging.info("upload file %s to bucket: %s", fileName, bucket)
        if not os.path.isfile(fileName):
            raise Exception('fileName: ' + fileName + 'not found')
        else:
            with open(fileName, 'rb') as objectData:
                try:
                    self.client.put_object(Body=objectData, Bucket=bucket, Key=key)
                except ClientError as e:
                    logging.warn(str(e))
                    raise Exception('fileName: ' + fileName + ' upload failed, err: ' + str(e))

    def download_file_from_s3(self, fileName, bucket, key):
        logging.info("download key  %s from bucket: %s as fileName %s", key, bucket, fileName)
        try:
            self.client.download_file(Bucket=bucket, Key=key, Filename=fileName)
        except ClientError as e:
            logging.warn(str(e))
            raise Exception('fileName: ' + fileName + 'download  failed, err: ' + str(e))
