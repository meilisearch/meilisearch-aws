import requests
import time
import boto3
from os.path import expanduser
import os
from datetime import datetime

import utils

### Setup environment and settings

MEILI_CLOUD_SCRIPTS_VERSION_TAG='v0.18.1'
BASE_OS_NAME='Debian-10.3'
SNAPSHOT_NAME="MeiliSearch-{}-{}".format(MEILI_CLOUD_SCRIPTS_VERSION_TAG, BASE_OS_NAME)
SSH_KEY='MarketplaceKeyPair'
INSTANCE_TYPE='t2.small'
SECURITY_GROUP='MarketplaceSecurityGroup'
DEBIAN_BASE_IMAGE_ID='ami-00000f9d1b75a36f8'

USER_DATA =requests.get(
    'https://raw.githubusercontent.com/meilisearch/cloud-scripts/{}/scripts/cloud-config.yaml'
    .format(MEILI_CLOUD_SCRIPTS_VERSION_TAG)
).text

ec2 = boto3.resource('ec2')

### Create EC2 instance to setup MeiliSearch

print('Creating AWS EC2 instance')
instances = ec2.create_instances(
    ImageId=DEBIAN_BASE_IMAGE_ID,
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

print('Waiting for AWS EC2 instance state to be "running"')
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

# Execute deploy script via SSH

commands = [
    'curl https://raw.githubusercontent.com/meilisearch/cloud-scripts/{0}/scripts/deploy-meilisearch.sh | sudo bash -s {0} {1}'.format(MEILI_CLOUD_SCRIPTS_VERSION_TAG, "AWS"),
]

for cmd in commands:
    ssh_command = 'ssh {user}@{host} -o StrictHostKeyChecking=no -i {ssh_key_path} "{cmd}"'.format(
        user='admin',
        host=instance.public_ip_address,
        ssh_key_path=expanduser('~') + '/Downloads/MarketplaceKeyPair.pem',
        cmd=cmd,
    )
    print("EXECUTE COMMAND:", ssh_command)
    os.system(ssh_command)
    time.sleep(5)

# Create AMI Image

print('Triggering AMI Image creation...')
image = boto3.client('ec2').create_image(
    InstanceId=instance.id,
    Name="{}-{}".format(SNAPSHOT_NAME, datetime.now().strftime("(%d-%m-%Y-%H-%M-%S)")),
    Description='Meilisearch {} running on {}.'.format(MEILI_CLOUD_SCRIPTS_VERSION_TAG, BASE_OS_NAME)
)
print('   AMI creation triggered: {}'.format(image['ImageId']))
