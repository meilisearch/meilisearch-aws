import requests
import time
import boto3

import utils

### Setup environment and settings

MEILI_CLOUD_SCRIPTS_VERSION_TAG='v0.18.1'

SSH_KEY='MarketplaceKeyPair'
INSTANCE_TYPE='t2.small'
SECURITY_GROUP='MarketplaceSecurityGroup'

USER_DATA =requests.get(
    'https://raw.githubusercontent.com/meilisearch/cloud-scripts/{}/scripts/cloud-config.yaml'
    .format(MEILI_CLOUD_SCRIPTS_VERSION_TAG)
).text

ec2 = boto3.resource('ec2')


### Create EC2 instance to setup MeiliSearch

print('Creating AWS EC2 instance')
instances = ec2.create_instances(
    ImageId='ami-00000f9d1b75a36f8',
    MinCount=1,
    MaxCount=1,
    InstanceType=INSTANCE_TYPE,
    KeyName=SSH_KEY,
    SecurityGroups=[
        SECURITY_GROUP,
    ],
    UserData=USER_DATA
)
print('   Instance created. ID: {}'.format(instances[0].id))


### Wait for EC2 instance to be 'running'

print('Waiting for AWS EC2 instance state to be 'running'')
instance = ec2.Instance(instances[0].id)
state_code, state = utils.wait_for_instance_running(instance, timeout_seconds=600)
print('   Instance state: {}'.format(instance.state['Name']))
if state_code == utils.STATUS_OK:
    print('   Instance IP: {}'.format(instance.public_ip_address))
else:
    print('   Error: {}. State: {}.'.format(state_code, state))
    utils.terminate_instance_and_exit(instance)


### Wait for Health check after configuration is finished

print('Waiting for MeiliSearch health check (may take a few minutes: config and reboot)')
health = utils.wait_for_health_check(instance, timeout_seconds=600)
if health == utils.STATUS_OK:
    print('   Instance is healthy')
else:
    print('   Timeout waiting for health check')
    utils.terminate_instance_and_exit(instance)
