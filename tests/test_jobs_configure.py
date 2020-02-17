import configparser
import jobs_configure
import unittest

# Test constants
CONFIG_INI = 'src/dev.ini'

EXPECTED_ALARM_CONFIGS = [
    {
        'alarmName': 'DownloadTimeUpperLimitAlarm',
        'jobId': 'JobPython5566',
        'namespace': 'IoT:OTA:JobExecution',
        'metricName': 'downloadTime',
        'stat': 'p99',
        'period': 60,
        'threshold': 3600.0,
        'alarmType': 'upper',
        'evaluationPeriods': 5,
        'datapointsToAlarm': 3,
        'alarmActions': [
            'arn:aws:sns:<region>:<aws-account-id>:email-notification',
            'arn:aws:sns:<region>:<aws-account-id>:sms-notification'
            ]
    },
    {
        'alarmName': 'DownloadTimeLowerLimitAlarm',
        'jobId': 'JobPython5566',
        'namespace': 'IoT:OTA:JobExecution',
        'metricName': 'downloadTime',
        'stat': 'p99',
        'period': 60,
        'threshold': 100.0,
        'alarmType': 'lower',
        'evaluationPeriods': 5,
        'datapointsToAlarm': 3,
        'alarmActions': ['arn:aws:sns:<region>:<aws-account-id>:ota-force-stopper']
    }
]


class JobsConfigureTests(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_INI)

    def test_alarm_configs_parser(self):
        status, result = jobs_configure.alarm_configs_parser(self.config)
        assert status
        assert EXPECTED_ALARM_CONFIGS == result
