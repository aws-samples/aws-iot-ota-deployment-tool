import json
import logging
import boto3
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client('cloudwatch')

def create_status_metric(event):
    return {
            'MetricName': event['status'].lower() + 'Count',
            'Dimensions': [
                {
                    'Name': 'jobId',
                    'Value': event['jobId']
                },
            ],
            'Timestamp': datetime.fromtimestamp(event['timestamp']),
            'Value': 1.0,
            'Unit': 'Count'
        }
        
def create_download_time_metric(event):
    return {
            'MetricName': 'downloadTime',
            'Dimensions': [
                {
                    'Name': 'jobId',
                    'Value': event['jobId']
                },
            ],
            'Timestamp': datetime.fromtimestamp(event['timestamp']),
            'Value': float(event['statusDetails']['downloadTime']),
            'Unit': 'Seconds'
        }

def lambda_handler(event, context):
    # TODO implement
    logger.info('Received event: %s', event)
    
    statusMetric = create_status_metric(event)
    downloadTimeMetric = create_download_time_metric(event)
    logger.info('Status metric: %s', statusMetric)
    logger.info('DownloadTime metric: %s', downloadTimeMetric)
    
    response = client.put_metric_data(
        Namespace='IoT:OTA:JobExecution',
        MetricData=[
            statusMetric,
            downloadTimeMetric
        ]
    )
    
    logger.info('CloudWatch Metrics Response: %s', response)

