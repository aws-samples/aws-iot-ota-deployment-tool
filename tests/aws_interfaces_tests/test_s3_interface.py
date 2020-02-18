import unittest
from unittest.mock import Mock, call
from unittest.mock import patch
from aws_interfaces.s3_interface import S3Interface
from botocore.exceptions import ClientError
from pathlib import Path


REGION = 'us-east-1'
FILE_NAME = 'test.bin'
BUCKET = 'testBucket'
KEY = 'testObjectName'
Path(FILE_NAME).touch()


class S3InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.s3_interface = S3Interface(REGION)
        self.s3_interface.client.put_object = Mock(return_value=None)
        self.s3_interface.client.download_file = Mock(return_value=None)

    def test_upload_file_to_s3(self):
        mock_open = unittest.mock.mock_open(read_data=None)

        # When this happens
        with unittest.mock.patch('builtins.open', mock_open):
            objectData = open(FILE_NAME, 'rb')
            self.s3_interface.upload_file_to_s3(fileName=FILE_NAME, bucket=BUCKET, key=KEY)

        # Expect these behaviors
        self.s3_interface.client.put_object.assert_called_with(Body=objectData, Bucket=BUCKET, Key=KEY)
        objectData.close()

    def test_upload_file_to_s3_file_not_exist(self):
        mock_open = unittest.mock.mock_open(read_data=None)

        # When this happens
        with unittest.mock.patch('builtins.open', mock_open):
            objectData = open(FILE_NAME, 'rb')
            with patch('os.path.isfile', return_value=False) as mocked_os:
                with self.assertRaises(Exception):
                    self.s3_interface.upload_file_to_s3(fileName=objectData, bucket=BUCKET, key=KEY)

        objectData.close()

    def test_upload_file_to_s3_exception(self):
        self.s3_interface.client.put_object = Mock(side_effect=ClientError({}, 'test'))
        mock_open = unittest.mock.mock_open(read_data=None)

        # When this happens
        with unittest.mock.patch('builtins.open', mock_open):
            objectData = open(FILE_NAME, 'rb')
            with self.assertRaises(Exception):
                self.s3_interface.upload_file_to_s3(fileName=FILE_NAME, bucket=BUCKET, key=KEY)

        # Expect these behaviors
        self.s3_interface.client.put_object.assert_called_with(Body=objectData, Bucket=BUCKET, Key=KEY)
        objectData.close()

    def test_download_file_from_s3(self):
        # When this happens
        self.s3_interface.download_file_from_s3(fileName=FILE_NAME, bucket=BUCKET, key=KEY)

        # Expect these behaviors
        self.s3_interface.client.download_file.assert_called_with(Bucket=BUCKET, Key=KEY, Filename=FILE_NAME)

    def test_download_file_from_s3_exception(self):
        self.s3_interface.client.download_file = Mock(side_effect=ClientError({}, 'test'))

        # When this happens
        with self.assertRaises(Exception):
            self.s3_interface.download_file_from_s3(fileName=FILE_NAME, bucket=BUCKET, key=KEY)

        # Expect these behaviors
        self.s3_interface.client.download_file.assert_called_with(Bucket=BUCKET, Key=KEY, Filename=FILE_NAME)
