import boto3
import datetime
import argparse
import logging
import sys

from aws_interfaces.s3_interface import S3Interface
from boto3.dynamodb.conditions import Key, Attr

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--region", action="store", required=True, dest="region", help="the region for uploading")
parser.add_argument("-tb", "--tableName", action="store", required=True, dest="tableName", help="the table for jobs entry")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
args = parser.parse_args()
region = args.region
tableName = args.tableName
s3 = boto3.client('s3', region_name=region)
dynamodb = boto3.client('dynamodb', region_name=region)
s3_interface = S3Interface(region)


def fetch_job():
    fe = Key('jobStatus').eq('PendingDeployment')
    tableJobConfigs = dynamodb.query(
        TableName=tableName,
        Limit=1,
        KeyConditionExpression="#S = :jobStatus",
        ExpressionAttributeNames={
            "#S": "jobStatus"
        },
        ExpressionAttributeValues={
            ":jobStatus": {"S": "PendingDeployment"}
        })
    for JobConfig in tableJobConfigs['Items']:
        bucket = JobConfig['bucketId']['S']
        s3_interface.download_file_from_s3('dev.ini', bucket, JobConfig['devFileKey']['S'])
        thingListFileKey = JobConfig['thingListFileKey']['S']
        tmp, thingListFileName = thingListFileKey.split('release/')
        s3_interface.download_file_from_s3(thingListFileName, bucket, thingListFileKey)
        binFileKey = JobConfig['binFileKey']['S']
        tmp, binName = binFileKey.split('release/')
        s3_interface.download_file_from_s3(binName, bucket, binFileKey)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        response = dynamodb.delete_item(
            TableName=tableName,
            Key={
                'jobStatus': JobConfig['jobStatus'],
                'timestamp': JobConfig['timestamp']
            }
        )
        if response is None:
            raise Exception('job record delete failed')
        else:
            jobStatus = 'Deployed'
            print(JobConfig['jobId'])
            dynamodb.put_item(
                TableName=tableName,
                Item={
                    'jobId': {'S': JobConfig['jobId']['S']},
                    'bucketId': {'S': JobConfig['bucketId']['S']},
                    'binFileKey': {'S': JobConfig['binFileKey']['S']},
                    'thingListFileKey': {'S': JobConfig['thingListFileKey']['S']},
                    'devFileKey': {'S': JobConfig['devFileKey']['S']},
                    'jobStatus': {'S': jobStatus},
                    'timestamp': {'S': timestamp}
                })
fetch_job()
