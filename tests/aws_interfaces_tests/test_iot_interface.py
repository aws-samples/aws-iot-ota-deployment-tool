import unittest
from unittest.mock import Mock, call
from aws_interfaces.iot_interface import IotInterface
from botocore.exceptions import ClientError

REGION = 'us-east-1'
STREAM_ID = 'testStremId'
FILE_ID = 'testFileId'
JOD_ID = 'JobPython5566'
BUCKET = 'testBucketNAme'
KEY = 'testKeyName'
ROLE_ARN = 'arn:aws:iam::123456789:role/ota_role'
THING_NAME = 'C-SDK'

TEST_DEFAULT_CONFIG = {
    'thingListFilePath': 'testThingList.txt',
    'binName': 'testBinNAme',
    'roleArn': ROLE_ARN,
    'jobId': JOD_ID,
    'rounds': 1,
    'bucket': BUCKET,
    'cleanUpCfg': False,
    'debug': False,
    'defaultDelay': 15,
    'useCustomJobDocument': False,
    'region':  'us-east-1',
    'fileChunkSize': 8192,
    'targetSelection': 'SNAPSHOT',
    'streamId': STREAM_ID,
    'binFileKey': 'testBinFileKey',
    'thingArnList': ['arn:aws:iot:us-east-1:482862934379:thing/CSDK-Thing'],
    'thingNameList': ['C-SDKThing'],
    'deviceCount': 1,
    'fileId': 'testFileId',
    'fileSize': 51200000,
    'jobDocumentSrc': 'https://temp.s3.amazonaws.com/job_temp.json'
}

TEST_PRESINGED_URL_CONFIG = {
    'roleArn': ROLE_ARN,
    'expiresInSec': 3600
}

TEST_EXECUTE_ROLLOUT_CONFIG = {
    'maximumPerMinute': 100,
    'useExponentialRateCfg': False,
    'EXP_RATE_CONFIG': {
        'baseRatePerMinute': 100,
        'incrementFactor': 2.0,
        'useRateIncreaseCriteria': True
    }
}

TEST_ABORT_CONFIG = {
    'criteriaList': [
        {
            'failureType': 'ALL',
            'action': 'CANCEL',
            'thresholdPercentage': 123.0,
            'minNumberOfExecutedThings': 123
        },
    ]
}

TEST_TIMEOUT_CONFIG = {
    'inProgressTimeoutInMinutes': 123
}


configMap = {
    'defaultConfig': TEST_DEFAULT_CONFIG,
    'presignedUrlConfig': TEST_PRESINGED_URL_CONFIG,
    'jobExecutionsRolloutConfig': TEST_EXECUTE_ROLLOUT_CONFIG,
    'abortConfig': TEST_ABORT_CONFIG,
    'timeoutConfig': TEST_TIMEOUT_CONFIG
}

TEST_EXPTECTED_DSB_JOB_RSP = {
    'job': {
        'status': 'CANCELED'
    }
}

TEST_EXPTECTED_DSB_JOB_RSP_IN_PROGRESS = {
    'job': {
        'status': 'IN_PROGRESS'
    }
}

TEST_EXPTECTED_DSB_JOB_EXEC_RSP = {
    'execution': 'testjobExecuteRsp'
}

TEST_EXPTECTED_DSB_STREAM_RSP = {
    'streamInfo': 'testStreamInfo'
}


class IotInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.iot_interface = IotInterface(REGION)
        self.iot_interface.client.create_stream = Mock(return_value=None)
        self.iot_interface.client.create_job = Mock(return_value=None)
        self.iot_interface.client.describe_job = Mock(return_value=TEST_EXPTECTED_DSB_JOB_RSP)
        self.iot_interface.client.describe_job_execution = Mock(return_value=TEST_EXPTECTED_DSB_JOB_EXEC_RSP)
        self.iot_interface.client.describe_stream = Mock(return_value=TEST_EXPTECTED_DSB_STREAM_RSP)
        self.iot_interface.client.cancel_job = Mock(return_value=None)
        self.iot_interface.client.delete_job = Mock(return_value=None)
        self.iot_interface.client.delete_stream = Mock(return_value=None)

    def test_create_stream(self):
        self.iot_interface.client.create_stream = Mock(return_value=TEST_EXPTECTED_DSB_JOB_RSP)

        # Given these inputs and expected outputs
        createStreamArgs = {
            'streamId': STREAM_ID,
            'fileId': FILE_ID,
            'bucket': BUCKET,
            'key': KEY,
            'role_arn': ROLE_ARN
        }

        iotCreateStreamArgs = {
            'streamId': STREAM_ID,
            'description': 'testing',
            'files': [
                {
                    "fileId": FILE_ID,
                    "s3Location": {
                        "bucket": BUCKET,
                        "key": KEY
                    }
                }
            ],
            'roleArn': ROLE_ARN
        }

        # When this happens
        status, err = self.iot_interface.create_stream(**createStreamArgs)

        # Expect these behaviors
        self.assertTrue(status)
        self.iot_interface.client.create_stream.assert_called_with(**iotCreateStreamArgs)

    def test_create_stream_exception(self):
        self.iot_interface.client.create_stream = Mock(side_effect=ClientError({}, 'test'))

        # Given these inputs and expected outputs
        createStreamArgs = {
            'streamId': STREAM_ID,
            'fileId': FILE_ID,
            'bucket': BUCKET,
            'key': KEY,
            'role_arn': ROLE_ARN
        }

        iotCreateStreamArgs = {
            'streamId': STREAM_ID,
            'description': 'testing',
            'files': [
                {
                    "fileId": FILE_ID,
                    "s3Location": {
                        "bucket": BUCKET,
                        "key": KEY
                    }
                }
            ],
            'roleArn': ROLE_ARN
        }

        # When this happens
        status, err = self.iot_interface.create_stream(**createStreamArgs)

        # Expect these behaviors
        self.assertFalse(status)
        self.iot_interface.client.create_stream.assert_called_with(**iotCreateStreamArgs)

    def test_create_job(self):
        # Given these inputs and expected outputs
        deployConfig = {}
        deployConfig['defaultConfig'] = configMap['defaultConfig']
        kwargs = {
            'jobId': TEST_DEFAULT_CONFIG['jobId'],
            'targets': TEST_DEFAULT_CONFIG['thingArnList'],
            'documentSource': TEST_DEFAULT_CONFIG['jobDocumentSrc'],
            'targetSelection': TEST_DEFAULT_CONFIG['targetSelection']
        }

        configList = [
            'presignedUrlConfig',
            'jobExecutionsRolloutConfig',
            'abortConfig',
            'timeoutConfig'
        ]
        # When this happens
        status, err = self.iot_interface.create_job(deployConfig)

        # Expect these behaviors
        self.assertTrue(status)
        self.iot_interface.client.create_job.assert_called_with(**kwargs)

        # add nore configs into test
        for configName in configList:
            with self.subTest(configName=configName):
                deployConfig[configName] = configMap[configName]
                kwargs[configName] = configMap[configName]

                # When this happens
                status, err = self.iot_interface.create_job(deployConfig)

                # Expect these behaviors
                self.assertTrue(status)
                assert not err
                self.iot_interface.client.create_job.assert_called_with(**kwargs)

    def test_create_job_exception(self):
        self.iot_interface.client.create_job = Mock(side_effect=ClientError({}, 'test'))

        # Given these inputs and expected outputs
        deployConfig = {}
        deployConfig['defaultConfig'] = configMap['defaultConfig']
        kwargs = {
            'jobId': TEST_DEFAULT_CONFIG['jobId'],
            'targets': TEST_DEFAULT_CONFIG['thingArnList'],
            'documentSource': TEST_DEFAULT_CONFIG['jobDocumentSrc'],
            'targetSelection': TEST_DEFAULT_CONFIG['targetSelection']
        }

        configList = [
            'presignedUrlConfig',
            'jobExecutionsRolloutConfig',
            'abortConfig',
            'timeoutConfig'
        ]

        for configName in configList:
            deployConfig[configName] = configMap[configName]
            kwargs[configName] = configMap[configName]

        # When this happens
        status, err = self.iot_interface.create_job(deployConfig)

        # Expect these behaviors
        self.assertFalse(status)
        self.iot_interface.client.create_job.assert_called_with(**kwargs)

    def test_get_job_info(self):
        # Given these inputs and expected outputs
        jobId = JOD_ID

        # When this happens
        job_dsb, err = self.iot_interface.get_job_info(jobId=jobId)

        # Expect these behaviors
        assert job_dsb == TEST_EXPTECTED_DSB_JOB_RSP['job']
        assert not err
        self.iot_interface.client.describe_job.assert_called_with(jobId=jobId)

    def test_get_job_info_exception(self):
        self.iot_interface.client.describe_job = Mock(side_effect=ClientError({}, 'test'))

        # Given these inputs and expected outputs
        jobId = JOD_ID

        # When this happens
        job_dsb, err = self.iot_interface.get_job_info(jobId=jobId)

        # Expect these behaviors
        assert job_dsb is None
        self.iot_interface.client.describe_job.assert_called_with(jobId=jobId)

    def test_get_job_exe_info(self):
        # Given these inputs and expected outputs
        jobId = JOD_ID
        thingName = THING_NAME

        # When this happens
        job_exe_dsb, err = self.iot_interface.get_job_exe_info(jobId=jobId, thingName=thingName)

        # Expect these behaviors
        assert job_exe_dsb == TEST_EXPTECTED_DSB_JOB_EXEC_RSP['execution']
        assert not err
        self.iot_interface.client.describe_job_execution.assert_called_with(jobId=jobId, thingName=thingName)

    def test_get_job_exe_info_exception(self):
        self.iot_interface.client.describe_job_execution = Mock(side_effect=ClientError({}, 'test'))

        # Given these inputs and expected outputs
        jobId = JOD_ID
        thingName = THING_NAME

        # When this happens
        job_exe_dsb, err = self.iot_interface.get_job_exe_info(jobId=jobId, thingName=thingName)

        # Expect these behaviors
        assert job_exe_dsb is None
        self.iot_interface.client.describe_job_execution.assert_called_with(jobId=jobId, thingName=thingName)

    def test_cancel_job(self):
        self.iot_interface.client.describe_job = Mock(
            side_effect=[
                TEST_EXPTECTED_DSB_JOB_RSP_IN_PROGRESS,
                TEST_EXPTECTED_DSB_JOB_RSP_IN_PROGRESS,
                TEST_EXPTECTED_DSB_JOB_RSP
            ]
        )

        # Given these inputs and expected outputs
        jobId = JOD_ID
        expectedCalls = [call(jobId=jobId), call(jobId=jobId), call(jobId=jobId)]

        # When this happens
        status, err = self.iot_interface.cancel_job(jobId=jobId)

        # Expect these behaviors
        self.assertTrue(status)
        assert not err
        self.iot_interface.client.cancel_job.assert_called_with(jobId=jobId)
        self.iot_interface.client.describe_job.assert_has_calls(expectedCalls)

    def test_cancel_job_exception(self):
        self.iot_interface.client.cancel_job = Mock(side_effect=ClientError({}, 'test'))

        # Given these inputs and expected outputs
        jobId = JOD_ID

        # When this happens
        status, _ = self.iot_interface.cancel_job(jobId=jobId)

        # Expect these behaviors
        self.assertFalse(status)
        self.iot_interface.client.cancel_job.assert_called_with(jobId=jobId)

    def test_job_is_deleting_while_cancel_job_is_called(self):
        self.iot_interface.client.describe_job = Mock(side_effect=ClientError({}, 'test'))

        # Given these inputs and expected outputs
        jobId = JOD_ID

        # When this happens
        status, err = self.iot_interface.cancel_job(jobId=jobId)

        # Expect these behaviors
        self.assertTrue(status)
        assert not err
        self.iot_interface.client.cancel_job.assert_called_with(jobId=jobId)
        self.iot_interface.client.describe_job.assert_called_once_with(jobId=jobId)

    def test_delete_job(self):
        self.iot_interface.client.describe_job = Mock(
            side_effect=[
                TEST_EXPTECTED_DSB_JOB_RSP,
                TEST_EXPTECTED_DSB_JOB_RSP,
                ClientError({}, 'test')
            ]
        )
        # Given these inputs and expected outputs
        jobId = JOD_ID
        expectedCalls = [call(jobId=jobId), call(jobId=jobId), call(jobId=jobId)]

        # When this happens
        status, err = self.iot_interface.delete_job(jobId=jobId)

        # Expect these behaviors
        self.assertTrue(status)
        assert not err
        self.iot_interface.client.delete_job.assert_called_with(jobId=jobId, force=True)
        self.iot_interface.client.describe_job.assert_has_calls(expectedCalls)

    def test_delete_job_exception(self):
        self.iot_interface.client.delete_job = Mock(side_effect=ClientError({}, 'test'))

        # Given these inputs and expected outputs
        jobId = JOD_ID

        # When this happens
        status, _ = self.iot_interface.delete_job(jobId=jobId)

        # Expect these behaviors
        self.assertFalse(status)
        self.iot_interface.client.delete_job.assert_called_with(jobId=jobId, force=True)

    def test_delete_stream(self):
        self.iot_interface.client.describe_stream = Mock(
            side_effect=[
                TEST_EXPTECTED_DSB_STREAM_RSP,
                TEST_EXPTECTED_DSB_STREAM_RSP,
                ClientError({}, 'test')
            ]
        )
        # Given these inputs and expected outputs
        streamId = STREAM_ID
        expectedCalls = [call(streamId=streamId), call(streamId=streamId), call(streamId=streamId)]

        # When this happens
        status, err = self.iot_interface.delete_stream(streamId=streamId)

        # Expect these behaviors
        self.assertTrue(status)
        assert not err
        self.iot_interface.client.delete_stream.assert_called_with(streamId=streamId)
        self.iot_interface.client.describe_stream.assert_has_calls(expectedCalls)

    def test_delete_stream_exception(self):
        self.iot_interface.client.delete_stream = Mock(side_effect=ClientError({}, 'test'))

        # Given these inputs and expected outputs
        streamId = STREAM_ID

        # When this happens
        status, _ = self.iot_interface.delete_stream(streamId=streamId)

        # Expect these behaviors
        self.assertFalse(status)
        self.iot_interface.client.delete_stream.assert_called_with(streamId=streamId)
