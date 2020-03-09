import unittest

from unittest.mock import Mock, call
from aws_interfaces.alarm_interface import AlarmInterface
from botocore.exceptions import ClientError

# Test constants
REGION = 'us-east-1'
ALARM_NAME = 'testAlarmName'
ALARM_NAME_ANOTHER = 'testAlarmNameAnother'
JOD_ID = 'testJodId'
NAMESPACE = 'testNamespace'
METRIC_NAME = 'testMetricName'
PERIOD = 60
STAT = 'Average'
PERCENTILE_STAT = 'p99.9'
THRESHOLD = 123.0
EVALUATION_PERIODS = 10
DATAPOINTS_TO_ALARM = 7
ALARM_ACTIONS = ['testAlarmAction1', 'testAlarmAction2']
GREATER_THAN_COMPARISON_OPERATOR = 'GreaterThanThreshold'
LESS_THAN_COMPARISON_OPERATOR = 'LessThanThreshold'
ALARM_TYPE_UPPER = 'upper'
ALARM_TYPE_LOWER = 'lower'


ALARM_CONFIG_BASE = {
    'alarmName': ALARM_NAME,
    'jobId': JOD_ID,
    'namespace': NAMESPACE,
    'metricName': METRIC_NAME,
    'period': PERIOD,
    'threshold': THRESHOLD,
    'evaluationPeriods': EVALUATION_PERIODS,
    'datapointsToAlarm': DATAPOINTS_TO_ALARM,
    'alarmActions': ALARM_ACTIONS
}

REQUEST_BASE = {
    'AlarmName': ALARM_NAME,
    'ActionsEnabled': True,
    'AlarmActions': ALARM_ACTIONS,
    'MetricName': METRIC_NAME,
    'Namespace': NAMESPACE,
    'Dimensions': [
        {
            'Name': 'jobId',
            'Value': JOD_ID
        }
    ],
    'Period': PERIOD,
    'Threshold': THRESHOLD,
    'EvaluationPeriods': EVALUATION_PERIODS,
    'DatapointsToAlarm': DATAPOINTS_TO_ALARM
}


class ALarmInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.alarm_interface = AlarmInterface(REGION)
        self.alarm_interface.client = Mock()

    def test_create_upper_limit_alarm(self):
        # Given these inputs and expected outputs
        alarmConfig = {
            'stat': STAT,
            'alarmType': ALARM_TYPE_UPPER,
            **ALARM_CONFIG_BASE
        }

        expectedRequest = {
            'Statistic': STAT,
            'ComparisonOperator': GREATER_THAN_COMPARISON_OPERATOR,
            **REQUEST_BASE
        }

        # When this happens
        assert (True, None) == self.alarm_interface.create_alarm(**alarmConfig)

        # Expect these behaviors
        self.alarm_interface.client.put_metric_alarm.assert_called_with(**expectedRequest)

    def test_create_upper_limit_alarm_with_percentile_stat(self):
        # Given these inputs and expected outputs
        alarmConfig = {
            'stat': PERCENTILE_STAT,
            'alarmType': ALARM_TYPE_UPPER,
            **ALARM_CONFIG_BASE
        }

        expectedRequest = {
            'ExtendedStatistic': PERCENTILE_STAT,
            'ComparisonOperator': GREATER_THAN_COMPARISON_OPERATOR,
            **REQUEST_BASE
        }

        # When this happens
        assert (True, None) == self.alarm_interface.create_alarm(**alarmConfig)

        # Expect these behaviors
        self.alarm_interface.client.put_metric_alarm.assert_called_with(**expectedRequest)

    def test_create_lower_limit_alarm(self):
        # Given these inputs and expected outputs
        alarmConfig = {
            'stat': STAT,
            'alarmType': ALARM_TYPE_LOWER,
            **ALARM_CONFIG_BASE
        }

        expectedRequest = {
            'Statistic': STAT,
            'ComparisonOperator': LESS_THAN_COMPARISON_OPERATOR,
            **REQUEST_BASE
        }

        # When this happens
        assert (True, None) == self.alarm_interface.create_alarm(**alarmConfig)

        # Expect these behaviors
        self.alarm_interface.client.put_metric_alarm.assert_called_with(**expectedRequest)

    def test_create_lower_limit_alarm_with_percentile_stat(self):
        # Given these inputs and expected outputs
        alarmConfig = {
            'stat': PERCENTILE_STAT,
            'alarmType': ALARM_TYPE_LOWER,
            **ALARM_CONFIG_BASE
        }

        expectedRequest = {
            'ExtendedStatistic': PERCENTILE_STAT,
            'ComparisonOperator': LESS_THAN_COMPARISON_OPERATOR,
            **REQUEST_BASE
        }

        # When this happens
        assert (True, None) == self.alarm_interface.create_alarm(**alarmConfig)

        # Expect these behaviors
        self.alarm_interface.client.put_metric_alarm.assert_called_with(**expectedRequest)

    def test_create_alarms(self):
        # Given these inputs and expected outputs
        alarmConfig1 = {
            'stat': PERCENTILE_STAT,
            'alarmType': ALARM_TYPE_LOWER,
            **ALARM_CONFIG_BASE
        }

        expectedRequest1 = {
            'ExtendedStatistic': PERCENTILE_STAT,
            'ComparisonOperator': LESS_THAN_COMPARISON_OPERATOR,
            **REQUEST_BASE
        }

        alarmConfig2 = {
            'stat': STAT,
            'alarmType': ALARM_TYPE_UPPER,
            **ALARM_CONFIG_BASE
        }

        expectedRequest2 = {
            'Statistic': STAT,
            'ComparisonOperator': GREATER_THAN_COMPARISON_OPERATOR,
            **REQUEST_BASE
        }

        alarmConfigs = [alarmConfig1, alarmConfig2]
        expectedCalls = [call(**expectedRequest1), call(**expectedRequest2)]

        # When this happens
        assert (True, None) == self.alarm_interface.create_alarms(alarmConfigs)

        # Expect these behaviors
        self.alarm_interface.client.put_metric_alarm.assert_has_calls(expectedCalls)

    def test_create_alarms_client_raises_error(self):
        # Given these inputs and expected outputs
        self.alarm_interface.client.put_metric_alarm = Mock(side_effect=ClientError({}, 'test'))

        alarmConfig = {
            'stat': PERCENTILE_STAT,
            'alarmType': ALARM_TYPE_LOWER,
            **ALARM_CONFIG_BASE
        }

        expectedRequest = {
            'ExtendedStatistic': PERCENTILE_STAT,
            'ComparisonOperator': LESS_THAN_COMPARISON_OPERATOR,
            **REQUEST_BASE
        }

        alarmConfigs = [alarmConfig]
        expectedCalls = [call(**expectedRequest)]

        # When this happens
        status, _ = self.alarm_interface.create_alarms(alarmConfigs)

        # Expect these behaviors
        assert not status
        self.alarm_interface.client.put_metric_alarm.assert_has_calls(expectedCalls)

    def test_delete_alarms(self):
        # Given these inputs and expected outputs
        alarmConfig1 = {
            'stat': PERCENTILE_STAT,
            'alarmType': ALARM_TYPE_LOWER,
            **ALARM_CONFIG_BASE
        }
        alarmConfig2 = {
            'stat': STAT,
            'alarmType': ALARM_TYPE_UPPER,
            **ALARM_CONFIG_BASE
        }
        alarmConfig2['alarmName'] = ALARM_NAME_ANOTHER

        alarmConfigs = [alarmConfig1, alarmConfig2]
        expectedRequest = [ALARM_NAME, ALARM_NAME_ANOTHER]

        # When this happens
        assert (True, None) == self.alarm_interface.delete_alarms(alarmConfigs)

        # Expect these behaviors
        self.alarm_interface.client.delete_alarms.assert_called_with(AlarmNames=expectedRequest)

    def test_delete_alarms_client_raises_error(self):
        # Given these inputs and expected outputs
        self.alarm_interface.client.delete_alarms = Mock(side_effect=ClientError({}, 'test'))

        alarmConfig1 = {
            'stat': PERCENTILE_STAT,
            'alarmType': ALARM_TYPE_LOWER,
            **ALARM_CONFIG_BASE
        }
        alarmConfig2 = {
            'stat': STAT,
            'alarmType': ALARM_TYPE_UPPER,
            **ALARM_CONFIG_BASE
        }
        alarmConfig2['alarmName'] = ALARM_NAME_ANOTHER

        alarmConfigs = [alarmConfig1, alarmConfig2]
        expectedRequest = [ALARM_NAME, ALARM_NAME_ANOTHER]

        # When this happens
        status, _ = self.alarm_interface.delete_alarms(alarmConfigs)

        # Expect these behaviors
        assert not status
        self.alarm_interface.client.delete_alarms.assert_called_with(AlarmNames=expectedRequest)
