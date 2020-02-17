from unittest.mock import patch
from lambda_handlers import metrics_generator
from datetime import datetime

TEST_EVENT = {
  'eventType': 'JOB_EXECUTION',
  'eventId': '1af19c20-98e9-463a-b497-9bcbab1dcb87',
  'timestamp': 1578368358,
  'operation': 'succeeded',
  'jobId': 'my-test-job5',
  'thingArn': 'arn:aws:iot:us-east-1:616261903601:thing/MyTestThingForOTA',
  'status': 'SUCCEEDED',
  'statusDetails': {
    'downloadTime': 120,
    'retryCount': 4
  }
}

TEST_EVENT_WITHOUT_RETRY_COUNT = {
  'eventType': 'JOB_EXECUTION',
  'eventId': '1af19c20-98e9-463a-b497-9bcbab1dcb87',
  'timestamp': 1578368358,
  'operation': 'succeeded',
  'jobId': 'my-test-job5',
  'thingArn': 'arn:aws:iot:us-east-1:616261903601:thing/MyTestThingForOTA',
  'status': 'SUCCEEDED',
  'statusDetails': {
    'downloadTime': 120
  }
}

EXPECTED_STATUS_METRIC = {
    'MetricName': 'succeededCount',
    'Dimensions': [
        {
            'Name': 'jobId',
            'Value': 'my-test-job5'
        },
    ],
    'Timestamp': datetime(2020, 1, 7, 11, 39, 18),
    'Value': 1.0,
    'Unit': 'Count'
}

EXPECTED_DOWNLOAD_TIME_METRIC = {
    'MetricName': 'downloadTime',
    'Dimensions': [
        {
            'Name': 'jobId',
            'Value': 'my-test-job5'
        },
    ],
    'Timestamp': datetime(2020, 1, 7, 11, 39, 18),
    'Value': 120.0,
    'Unit': 'Seconds'
}

EXPECTED_RETRY_COUNT_METRIC = {
    'MetricName': 'retryCount',
    'Dimensions': [
        {
            'Name': 'jobId',
            'Value': 'my-test-job5'
        },
    ],
    'Timestamp': datetime(2020, 1, 7, 11, 39, 18),
    'Value': 4,
    'Unit': 'Count'
}


@patch.object(metrics_generator.client, 'put_metric_data', return_value=200)
def test_lambda_handler(mock_method):
    expectedMetrics = [
        EXPECTED_STATUS_METRIC,
        EXPECTED_DOWNLOAD_TIME_METRIC,
        EXPECTED_RETRY_COUNT_METRIC
    ]
    metrics_generator.lambda_handler(TEST_EVENT, {})

    mock_method.assert_called_with(Namespace='IoT:OTA:JobExecution',
                                   MetricData=expectedMetrics)


@patch.object(metrics_generator.client, 'put_metric_data', return_value=200)
def test_lambda_handler_no_retry_count(mock_method):
    expectedMetrics = [
        EXPECTED_STATUS_METRIC,
        EXPECTED_DOWNLOAD_TIME_METRIC
    ]
    metrics_generator.lambda_handler(TEST_EVENT_WITHOUT_RETRY_COUNT, {})

    mock_method.assert_called_with(Namespace='IoT:OTA:JobExecution',
                                   MetricData=expectedMetrics)
