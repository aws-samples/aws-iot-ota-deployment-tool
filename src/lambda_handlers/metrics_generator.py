import logging
import boto3

from datetime import datetime

TIMESTAMP_KEY = 'timestamp'
JOB_ID_KEY = 'jobId'
STATUS_KEY = 'status'
STATUS_DETAILS_KEY = 'statusDetails'
DOWNLOAD_TIME_KEY = 'downloadTime'
RETRY_COUNT_KEY = 'retryCount'

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client('cloudwatch')


def create_status_metric(event, metricName):
    return {
            'MetricName': metricName,
            'Dimensions': [
                {
                    'Name': 'jobId',
                    'Value': event[JOB_ID_KEY]
                },
            ],
            'Timestamp': datetime.fromtimestamp(event[TIMESTAMP_KEY]),
            'Value': 1.0,
            'Unit': 'Count'
        }


def create_download_time_metric(event, metricName):
    try:
        return {
                'MetricName': metricName,
                'Dimensions': [
                    {
                        'Name': 'jobId',
                        'Value': event[JOB_ID_KEY]
                    },
                ],
                'Timestamp': datetime.fromtimestamp(event[TIMESTAMP_KEY]),
                'Value': float(event[STATUS_DETAILS_KEY][DOWNLOAD_TIME_KEY]),
                'Unit': 'Seconds'
            }
    except Exception as e:
        logger.error('Failed to create download time metric: %s', e)


def create_retry_count_metric(event, metricName):
    try:
        return {
                'MetricName': metricName,
                'Dimensions': [
                    {
                        'Name': 'jobId',
                        'Value': event[JOB_ID_KEY]
                    },
                ],
                'Timestamp': datetime.fromtimestamp(event[TIMESTAMP_KEY]),
                'Value': int(event[STATUS_DETAILS_KEY][RETRY_COUNT_KEY]),
                'Unit': 'Count'
            }
    except Exception as e:
        logger.error('Failed to create retry count metric: %s', e)


def add_metric(metricName, metricCreator, metricList, event):
    new_metric = metricCreator(event, metricName)
    if new_metric is not None:
        metricList.append(new_metric)
        logger.info('Metric %s created: %s', metricName, new_metric)
    else:
        logger.warn('Failed to create metric %s!')


def lambda_handler(event, context):
    logger.info('Received event: %s', event)

    metricList = []
    add_metric(event['status'].lower() + 'Count', create_status_metric, metricList, event)

    if STATUS_DETAILS_KEY in event:
        if DOWNLOAD_TIME_KEY in event[STATUS_DETAILS_KEY]:
            add_metric('downloadTime', create_download_time_metric, metricList, event)
        if RETRY_COUNT_KEY in event[STATUS_DETAILS_KEY]:
            add_metric('retryCount', create_retry_count_metric, metricList, event)

    response = client.put_metric_data(
        Namespace='IoT:OTA:JobExecution',
        MetricData=metricList
    )
    logger.info('CloudWatch Metrics Response: %s', response)
