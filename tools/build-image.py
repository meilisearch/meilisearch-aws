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
DEBIAN_BASE_IMAGE_ID='ami-003f19e0e687de1cd'

USER_DATA =requests.get(
    'https://raw.githubusercontent.com/meilisearch/cloud-scripts/{}/scripts/cloud-config.yaml'
    .format(MEILI_CLOUD_SCRIPTS_VERSION_TAG)
).text

SNAPSHOT_NAME="MeiliSearch-{}-{}".format(MEILI_CLOUD_SCRIPTS_VERSION_TAG, BASE_OS_NAME)
AMI_BUILD_NAME="{}-BUILD-{}".format(SNAPSHOT_NAME, datetime.now().strftime("(%d-%m-%Y-%H-%M-%S)"))
IMAGE_DESCRIPTION_NAME="MeiliSearch-{} running on {}".format(MEILI_CLOUD_SCRIPTS_VERSION_TAG, BASE_OS_NAME)

INSTANCE_TYPE='t2.small'
SECURITY_GROUP='MarketplaceSecurityGroup'

SSH_KEY='MarketplaceKeyPair-NVirginia'
SSH_KEY_PEM_FILE=expanduser('~') + '/.aws/KeyPairs/MarketplaceKeyPair-NVirginia.pem'
SSH_USER='admin'

AWS_DEFAULT_REGION='us-east-1'
AWS_REGIONS = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'af-south-1',
    'ap-east-1',
    'ap-south-1',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-northeast-1',
    'ca-central-1',
    'eu-central-1',
    'eu-west-1',
    'eu-west-2',
    'eu-south-1',
    'eu-west-3',
    'eu-north-1',
    'me-south-1',
    'sa-east-1',
]

AWS_REGION_AMIS = {}
UNSUCCESSFUL_AWS_REGION_AMIS = {}

ec2 = boto3.resource('ec2', AWS_DEFAULT_REGION)

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
state_code, state = utils.wait_for_instance_running(instance, AWS_DEFAULT_REGION, timeout_seconds=600)
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

### Execute deploy script via SSH

commands = [
    'curl https://raw.githubusercontent.com/meilisearch/cloud-scripts/{0}/scripts/deploy-meilisearch.sh | sudo bash -s {0} {1}'.format(MEILI_CLOUD_SCRIPTS_VERSION_TAG, "AWS"),
]

for cmd in commands:
    ssh_command = 'ssh {user}@{host} -o StrictHostKeyChecking=no -i {ssh_key_path} "{cmd}"'.format(
        user=SSH_USER,
        host=instance.public_ip_address,
        ssh_key_path=SSH_KEY_PEM_FILE,
        cmd=cmd,
    )
    print("EXECUTE COMMAND:", ssh_command)
    os.system(ssh_command)
    time.sleep(5)

### Create AMI Image

print('Triggering AMI Image creation...')
image = boto3.client('ec2', AWS_DEFAULT_REGION).create_image(
    InstanceId=instance.id,
    Name=AMI_BUILD_NAME,
    Description='Meilisearch {} running on {}.'.format(MEILI_CLOUD_SCRIPTS_VERSION_TAG, BASE_OS_NAME)
)
print('   AMI creation triggered: {}'.format(image['ImageId']))

### Wait for AMI creation

print("Waiting for AMI creation...")
state_code, ami = utils.wait_for_ami_available(image['ImageId'], AWS_DEFAULT_REGION)
if state_code == utils.STATUS_OK:
    print('   AMI created: {}'.format(image['ImageId']))
else:
    print('   Error: {}. State: {}.'.format(state_code, ami.state))
    utils.terminate_instance_and_exit(instance)

### Terminate EC2 Instance

print("Terminating instance...")
instance.terminate()

### Copy AMI to different AWS regions

print("Triggering AMI propagation worldwide...")
for aws_region in AWS_REGIONS:
    client = boto3.client('ec2', aws_region)
    response = client.copy_image(
        Name=SNAPSHOT_NAME,
        Description=IMAGE_DESCRIPTION_NAME,
        Encrypted=False,
        SourceImageId=image['ImageId'],
        SourceRegion=AWS_DEFAULT_REGION
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        AWS_REGION_AMIS[aws_region] = response['ImageId']
        print('   AMI copy triggered: {} - {}'.format(aws_region, response['ImageId']))
    else:
        print('   Error: AMI couldn\t be created for: {}.'.format(aws_region))
        print('   {}'.format(response['ResponseMetadata']['HTTPStatusCode']))

### Wait for propagated AMIs creation

print("Waiting for each AWS region AMI creation...")
for region, propagated_ami in AWS_REGION_AMIS.items():
    state_code, ami = utils.wait_for_ami_available(propagated_ami, region)
    if state_code == utils.STATUS_OK:
        print('   AMI created: {} - {}'.format(region, propagated_ami))
    else:
        print('   Error: {} - {}.'.format(region, propagated_ami))
        del AWS_REGION_AMIS[region]
        UNSUCCESSFUL_AWS_REGION_AMIS[region] = propagated_ami

### Make propagatedd AMIs public
print("Making each AMI Public...")
for region, propagated_ami in AWS_REGION_AMIS.items():
    state_code, public = utils.make_ami_public(propagated_ami, region)
    if state_code == utils.STATUS_OK:
        print('   AMI published: {} - {}'.format(region, propagated_ami))
    else:
        print('   Error: {} - {}.'.format(region, propagated_ami))
        del AWS_REGION_AMIS[region]
        UNSUCCESSFUL_AWS_REGION_AMIS[region] = propagated_ami

print('Successfully created {} AMIs:'.format(len(AWS_REGION_AMIS)))
for region, propagated_ami in AWS_REGION_AMIS.items():
    print('   {}'.format(region))
print('Error creating {} AMIs:'.format(len(UNSUCCESSFUL_AWS_REGION_AMIS)))
for region, propagated_ami in UNSUCCESSFUL_AWS_REGION_AMIS.items():
    print('   {}'.format(region))
