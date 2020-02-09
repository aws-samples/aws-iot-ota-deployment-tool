import argparse
import boto3
import configparser
import fileinput
import json
import logging
import os
import psutil
import re
import sys
import time
import uuid
from shutil import copyfile


def init_config(path):
    if os.path.isfile(path):
        config = configparser.ConfigParser()
        config.read(path)
    return config


def init_iot_client(credential):
    return boto3.client(
        'iot',
        aws_access_key_id=credential['awsAccessKeyId'],
        aws_secret_access_key=credential['awsSecretAccessKey'],
        region_name=credential['region']
    )


def build_and_run_client(iotClient, iotConfig):
    #create test policy
    try:
        iotClient.get_policy(
            policyName=iotConfig['devicePolicy']
        )
    except iotClient.exceptions.ResourceNotFoundException as e:
        logging.info('Create test policy %s', iotConfig['devicePolicy'])
        iotClient.create_policy(
            policyName=iotConfig['devicePolicy'],
            policyDocument=json.dumps({
                'Version': '2012-10-17',
                'Statement': [{
                    'Effect': 'Allow',
                    'Action': 'iot:*',
                    'Resource': '*'
                }]
            })
        )
    # create test thing group
    try:
        iotClient.describe_thing_group(thingGroupName=iotConfig['thingGroup'])
    except iotClient.exceptions.ResourceNotFoundException as e:
        logging.info('Create test thing group %s', iotConfig['thingGroup'])
        iotClient.create_thing_group(thingGroupName=iotConfig['thingGroup'])

    # create thing
    client_id = str(uuid.uuid4())
    thing_name = 'stressTest_%s' % client_id
    iotClient.create_thing(thingName=thing_name)
    iotClient.add_thing_to_thing_group(
        thingGroupName=iotConfig['thingGroup'], thingName=thing_name
    )
    resp = iotClient.create_keys_and_certificate(setAsActive=True)
    certificateArn = resp['certificateArn']
    thing_cert = '%s/%s.pem.crt' % (iotConfig['thingCertDir'], client_id)
    thing_key = '%s/%s.pem.key' % (iotConfig['thingCertDir'], client_id)
    with open(thing_cert, 'w') as f:
        f.write(resp['certificatePem'])
    with open(thing_key, 'w') as f:
        f.write(resp['keyPair']['PrivateKey'])
    rootCAPath = '%s/%s' % (iotConfig['thingCertDir'], os.path.basename(iotConfig['rootCA']))
    copyfile(iotConfig['rootCA'], rootCAPath)
    iotClient.attach_thing_principal(
        thingName=thing_name,
        principal=certificateArn
    )
    iotClient.attach_policy(
        policyName=iotConfig['devicePolicy'],
        target=certificateArn
    )
    endpoint = iotClient.describe_endpoint(endpointType='iot:Data-ATS')['endpointAddress']

    # change config
    configs_map = {
        'AWS_IOT_MQTT_HOST':            'AWS_IOT_MQTT_HOST              "%s"' % endpoint,
        'AWS_IOT_MQTT_CLIENT_ID':       'AWS_IOT_MQTT_CLIENT_ID         "%s"' % client_id,
        'AWS_IOT_MY_THING_NAME':        'AWS_IOT_MY_THING_NAME          "%s"' % thing_name,
        'AWS_IOT_ROOT_CA_FILENAME':     'AWS_IOT_ROOT_CA_FILENAME       "%s"' % os.path.basename(rootCAPath),
        'AWS_IOT_CERTIFICATE_FILENAME': 'AWS_IOT_CERTIFICATE_FILENAME   "%s"' % os.path.basename(thing_cert),
        'AWS_IOT_PRIVATE_KEY_FILENAME': 'AWS_IOT_PRIVATE_KEY_FILENAME   "%s"' % os.path.basename(thing_key)
    }
    for line in fileinput.input(iotConfig['iotConfigPath'], inplace=True):
        for src, dest in configs_map.items():
            if src in line:
                line = re.sub(src + '.*', dest, line)
                break
        sys.stdout.write(line)

    # build
    work_dir = os.getcwd()
    sample_dir = os.path.dirname(iotConfig['iotConfigPath'])
    sample_name = os.path.basename(sample_dir)
    os.chdir(sample_dir)
    os.system('make')
    os.rename(sample_name, client_id)

    # run
    os.system('./%s &' % client_id)
    os.chdir(work_dir)

    return client_id


def clean(iotClient, iotConfig, all=True, number=0):
    resp = iotClient.list_things_in_thing_group(thingGroupName=iotConfig['thingGroup'])
    things = resp['things']
    while 'nextToken' in resp:
        resp = iotClient.list_things_in_thing_group(
            thingGroupName=iotConfig['thingGroup'],
            nextToken=resp['nextToken']
        )
        things.extend(resp['things'])

    sample_dir = os.path.dirname(iotConfig['iotConfigPath'])
    for thing_name in things:
        resp = iotClient.list_thing_principals(
            thingName=thing_name
        )
        certificateIds = []
        for principal in resp['principals']:
            certificateId = principal.split('/')[-1]
            certificateIds.append(certificateId)
            iotClient.detach_policy(
                policyName=iotConfig['devicePolicy'], target=principal
            )
            iotClient.update_certificate(
                certificateId=certificateId, newStatus='INACTIVE'
            )
            iotClient.detach_thing_principal(
                thingName=thing_name,
                principal=principal
            )
        # wait for detach finish
        while True:
            resp = iotClient.list_thing_principals(
                thingName=thing_name
            )
            if not resp['principals']:
                break
            time.sleep(1)
        for certificateId in certificateIds:
            iotClient.delete_certificate(certificateId=certificateId, forceDelete=True)
        iotClient.delete_thing(thingName=thing_name)

        client_id = thing_name.split('_', 1)[-1]
        os.remove('%s/%s.pem.crt' % (iotConfig['thingCertDir'], client_id))
        os.remove('%s/%s.pem.key' % (iotConfig['thingCertDir'], client_id))
        os.remove('%s/%s' % (sample_dir, client_id))
        for proc in psutil.process_iter():
            if proc.name() == client_id:
                proc.kill()


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--ini", action="store", required=True, dest="ini", help="config file path")
parser.add_argument("-a", "--action", action="store", required=True, dest="action", help="deploy or clean")
parser.add_argument("-n", "--number", action="store", type=int, dest="number", help="number of devices")
args = parser.parse_args()
number = args.number
config = init_config(args.ini)
client_limit = int(config['IOT']['clientLimit'])

if args.action == 'deploy':
    if not number:
        msg = 'Need to specify number of device to deploy'
        logging.error(msg)
        rasie Exception(msg)
    elif number > client_limit:
        msg = 'Exceed limit %s. Expect deploy %d devices.' % (number, client_limit)
        logging.error(msg)
        raise Exception(msg)
    iotClient = init_iot_client(config['CREDENTIAL'])
    for _ in range(number):
        build_and_run_client(iotClient, config['IOT'])
elif args.action == 'clean':
    iotClient = init_iot_client(config['CREDENTIAL'])
    clean(iotClient, config['IOT'])
