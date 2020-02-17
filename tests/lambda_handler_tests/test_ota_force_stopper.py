from unittest.mock import patch
from lambda_handlers import ota_force_stopper

TEST_EVENT = {
    'Records': [{
        'EventSource': 'aws:sns',
        'EventSubscriptionArn': 'arn:aws:sns:us-east-1:616261903601:test-topic-ota:168f5a1e-7e42-4b18-9e9a-ad394939641b',
        'EventVersion': '1.0',
        'Sns': {
            'Message': '{"AlarmName":"My-Test-Alarm","AlarmDescription":null,"AWSAccountId":"616261903601",'
                       '"NewStateValue":"ALARM","NewStateReason":"Threshold '
                       'Crossed: 1 out of the last 1 datapoints [4000.0 (06/02/20 03:09:00)] was greater '
                       'than the threshold (3000.0) (minimum 1 datapoint for OK -> ALARM '
                       'transition).","StateChangeTime":"2020-02-06T03:10:09.199+0000","Region":"US East (N. '
                       'Virginia)","OldStateValue":"OK","Trigger":{"MetricName":"downloadTime","Namespace":"IoT:OTA:JobExecution"'
                       ',"StatisticType":"Statistic","Statistic":"MAXIMUM","Unit":null,"Dimensions":'
                       '[{"value":"my-test-job-1001","name":"jobId"}],"Period":60,"EvaluationPeriods":1,"ComparisonOperator"'
                       ':"GreaterThanThreshold","Threshold":3000.0,"TreatMissingData":"- TreatMissingData:                    '
                       'notBreaching","EvaluateLowSampleCountPercentile":""}}',
            'MessageAttributes': {},
            'MessageId': '587afb8b-ae6f-55e8-bdbd-ad3e2bbe0f21',
            'Signature': 'FC1vlvlptCN771AQWu2UrntcT3Icy6y5hlJALUDfzO05iC40MQ3IssB2nx/pf0d2pItz5C+w5+/5XNf+F+Ary/'
                         'bgW8aUSLGRmghpPuIiCKmp4d3wdSCPzrE667bdrpeK6HHI8FG/kU6VBhp6EaV+pyaKU7udnIcBd5ENEP9hKHMR'
                         'ILmFYo8kCKqZa4HnlHeT+OI2RQY7oLZA4mQpczddUjOFHIQ/B+g4unlaK+NL2zW+gLQ+/y5b7xnPNGTyAr0ZOy'
                         'eBjpK79nbm7ZrbamXUz+/Fg8vNcGEBjvOzsRmcEqL8WGHgWZBq6D74Na7m5U4rQMURzyaQMcM9ZVN1WacF8A==',
            'SignatureVersion': '1',
            'SigningCertUrl': 'https://sns.us-east-1.amazonaws.com/SimpleNotificationService-a86cb10b4e1f29c941702d737128f7b6.pem',
            'Subject': 'ALARM: "My-Test-Alarm" in US East (N. Virginia)',
            'Timestamp': '2020-02-06T03:10:09.246Z',
            'TopicArn': 'arn:aws:sns:us-east-1:616261903601:test-topic-ota',
            'Type': 'Notification',
            'UnsubscribeUrl': 'https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:616261'
                              '903601:test-topic-ota:168f5a1e-7e42-4b18-9e9a-ad394939641b'
            }
        }
    ]
}


@patch.object(ota_force_stopper.client, 'cancel_job', return_value=200)
def test_lambda_handler(mock_method):
    ota_force_stopper.lambda_handler(TEST_EVENT, {})

    mock_method.assert_called_with(
        jobId="my-test-job-1001",
        comment='Alarm "My-Test-Alarm" is in ALARM state.',
        force=True)
