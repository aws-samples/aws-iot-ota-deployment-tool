import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)
client = boto3.client('iot')


def lambda_handler(event, context):
    logger.info('Received event: %s', event)

    for record in event['Records']:
        alarmEvent = json.loads(record['Sns']['Message'])
        jobIdDimension = [x for x in alarmEvent['Trigger']['Dimensions'] if x['name'] == "jobId"].pop()
        jobId = jobIdDimension['value']
        logger.info('Force stopping job: %s', jobId)

        response = client.cancel_job(
            jobId=jobId,
            comment='Alarm "%s" is in ALARM state.' % alarmEvent['AlarmName'],
            force=True
        )
        logger.info('IoT Core Response: %s', response)
