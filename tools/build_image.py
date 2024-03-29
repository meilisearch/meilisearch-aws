import sys
import boto3
import utils
import config

ec2 = boto3.resource('ec2', config.AWS_DEFAULT_REGION)

# Remove analytics for CI jobs

if len(sys.argv) > 1 and '--no-analytics' in sys.argv:
    print('Launch build image without analytics.')
    index = config.USER_DATA.find('--env development')
    USER_DATA = config.USER_DATA[:index] + '--no-analytics ' + config.USER_DATA[index:]
else:
    USER_DATA = config.USER_DATA

# Create EC2 instance to setup Meilisearch

print('Creating AWS EC2 instance')
instances = ec2.create_instances(
    ImageId=config.DEBIAN_BASE_IMAGE_ID,
    MinCount=1,
    MaxCount=1,
    InstanceType=config.INSTANCE_TYPE,
    SecurityGroups=[
        config.SECURITY_GROUP,
    ],
    UserData=USER_DATA
)
print(f'   Instance created. ID: {instances[0].id}')


# Wait for EC2 instance to be 'running'

print('Waiting for AWS EC2 instance state to be "running"')
instance = ec2.Instance(instances[0].id)
state_code, state = utils.wait_for_instance_running(
    instance, config.AWS_DEFAULT_REGION, timeout_seconds=600)
print(f"   Instance state: {instance.state['Name']}")
if state_code == utils.STATUS_OK:
    print(f'   Instance IP: {instance.public_ip_address}')
else:
    print(f'   Error: {state_code}. State: {state}.')
    utils.terminate_instance_and_exit(instance)


# Wait for Health check after configuration is finished

print('Waiting for Meilisearch health check (may take a few minutes: config and reboot)')
HEALTH = utils.wait_for_health_check(instance, timeout_seconds=600)
if HEALTH == utils.STATUS_OK:
    print('   Instance is healthy')
else:
    print('   Timeout waiting for health check')
    utils.terminate_instance_and_exit(instance)

# Check version

print('Waiting for Version check')
try:
    utils.check_meilisearch_version(
        instance, config.MEILI_CLOUD_SCRIPTS_VERSION_TAG)
except Exception as err:
    print(f"   Exception: {err}")
    utils.terminate_instance_and_exit(instance)
print('   Version of Meilisearch match!')

# Create AMI Image

if len(sys.argv) > 1 and sys.argv[1] != '--no-analytics':
    AMI_BUILD_NAME = sys.argv[1]
else:
    AMI_BUILD_NAME = config.AMI_BUILD_NAME

print('Triggering AMI Image creation...')
image = boto3.client('ec2', config.AWS_DEFAULT_REGION).create_image(
    InstanceId=instance.id,
    Name=AMI_BUILD_NAME,
    Description=f'Meilisearch {config.MEILI_CLOUD_SCRIPTS_VERSION_TAG} running on {config.BASE_OS_NAME}.'
)
print(f"   AMI creation triggered: {image['ImageId']}")

# Wait for AMI creation

print('Waiting for AMI creation...')
state_code, ami = utils.wait_for_ami_available(
    image['ImageId'], config.AWS_DEFAULT_REGION)
if state_code == utils.STATUS_OK:
    print(f"   AMI created: {image['ImageId']}")
else:
    print(f'   Error: {state_code}. State: {ami.state}.')
    utils.terminate_instance_and_exit(instance)

# Terminate EC2 Instance

print('Terminating instance...')
instance.terminate()
print('   Instance terminated')
