import boto3
import logging
import sys

from botocore.exceptions import ClientError

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class AlarmInterface:
    def __init__(self, region):
        self.client = boto3.client('cloudwatch', region_name=region)

    def _create_alarm_base(self, alarmName, jobId, namespace, metricName, period,
                           stat, evaluationPeriods, datapointsToAlarm,
                           alarmActions):
        alarmBase = {
            'AlarmName': alarmName,
            'ActionsEnabled': True,
            'AlarmActions': alarmActions,
            'MetricName': metricName,
            'Namespace': namespace,
            'Dimensions': [
                {
                    'Name': 'jobId',
                    'Value': jobId
                }
            ],
            'Period': period,
            'EvaluationPeriods': evaluationPeriods,
            'DatapointsToAlarm': datapointsToAlarm
        }

        # Percentile statistics should be put under 'ExtendedStatistic'
        if stat.startswith('p'):
            alarmBase['ExtendedStatistic'] = stat
        else:
            alarmBase['Statistic'] = stat

        return alarmBase

    def create_alarm(self, alarmName, jobId, namespace, metricName, period, stat,
                     threshold, alarmType, evaluationPeriods, datapointsToAlarm,
                     alarmActions):
        logging.info('Creating alarm: metric=%s, stat=%s, threshold=%s, type=%s',
                     metricName, stat, threshold, alarmType)

        alarmBase = self._create_alarm_base(alarmName, jobId, namespace, metricName,
                                            period, stat, evaluationPeriods,
                                            datapointsToAlarm, alarmActions)

        requestPayload = {
                'Threshold': threshold,
                **alarmBase
            }

        if alarmType == 'upper':
            requestPayload['ComparisonOperator'] = 'GreaterThanThreshold'
        else:
            requestPayload['ComparisonOperator'] = 'LessThanThreshold'

        try:
            self.client.put_metric_alarm(**requestPayload)
        except ClientError as e:
            return False, str(e)
        return True, None

    def create_alarms(self, alarmConfigs):
        '''
        Directly takes in a list of alarmConfig dictionary payload and create alarm for
        each of the configs.

        alarmConfigs = [
            {
                alarmName: String,
                jobId: String,
                namespace: String,
                metricName: String,
                period: Int,
                stat: String,
                threshold: Float,
                alarmType: String,
                evaluationPeriods: Int,
                datapointsToAlarm: Int,
                alarmActions: [arn: String]
            },
        ]
        '''
        for alarmConfig in alarmConfigs:
            status, err = self.create_alarm(**alarmConfig)
            if not status:
                logging.error(err)
                return False, 'Failed creating alarms'
        return True, None

    def delete_alarms(self, alarmConfigs):
        '''
        Delete alarms specified by a list of alarmConfigs.

        alarmConfigs = [
            {
                alarmName: String,
                jobId: String,
                namespace: String,
                metricName: String,
                period: Int,
                stat: String,
                threshold: Float,
                alarmType: String,
                evaluationPeriods: Int,
                datapointsToAlarm: Int,
                alarmActions: [arn: String]
            },
        ]
        '''
        alarmNames = [alarmConfig['alarmName'] for alarmConfig in alarmConfigs]
        logging.info('Deleting alarms: %s', str(alarmNames))

        try:
            self.client.delete_alarms(alarmNames)
        except ClientError as e:
            return False, str(e)
        return True, None
