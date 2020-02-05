import json
import boto3
import time
import logging
import sys
import logging
from botocore.exceptions import ClientError


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
s3 = boto3.client('s3')


def upload_file_to_s3(fileName, bucket, key):
    global s3
    logging.info( "upload file %s to bucket: %s", fileName, bucket)
    try:
        with open(fileName, 'rb') as objectData:
            s3.put_object(Body=objectData, Bucket=bucket, Key=key)
    except ClientError as e:
        logging.warn(str(e))
        raise Exception('fileName: ' + fileName + ' upload binFile failed' )
    return True


def download_file_from_s3(fileName, bucket, objectName):
    global s3
    logging.info( "download objectName  %s from bucket: %s as fileName %s", objectName, bucket, fileName)
    try:
        s3.download_file(bucket, objectName, fileName)
    except ClientError as e:
        logging.warn(str(e))
        return False
    return True


def init(region):
    global s3
    s3 = boto3.client('s3', region_name=region)

