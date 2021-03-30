import sys
import boto3
import utils
import config

ec2 = boto3.resource('ec2', config.AWS_DEFAULT_REGION)

if len(sys.argv) > 1:
    SNAPSHOT_NAME = sys.argv[1]
else:
    raise Exception("No snapshot name specified")

print("Running test for image named: {name}...".format(
    name=SNAPSHOT_NAME))

# Get the image for the test

MEILI_IMG = None
images = boto3.client('ec2', config.AWS_DEFAULT_REGION).describe_images(
    Owners=['self'])['Images']
for img in images:
    if img['Name'] == SNAPSHOT_NAME:
        MEILI_IMG = boto3.resource(
            'ec2', config.AWS_DEFAULT_REGION).Image(id=img['ImageId'])
        print("Found image: {name} created at {creation_date}".format(
            name=MEILI_IMG.name,
            creation_date=MEILI_IMG.creation_date
        ))
        break

if MEILI_IMG is None:
    raise Exception("Couldn't find the specified image: {}".format(
        SNAPSHOT_NAME))

# Create EC2 instance from the retreived image

print('Creating AWS EC2 instance from image')
instances = ec2.create_instances(
    ImageId=MEILI_IMG.id,
    MinCount=1,
    MaxCount=1,
    InstanceType=config.INSTANCE_TYPE,
    SecurityGroups=[
        config.SECURITY_GROUP,
    ]
)
print('   Instance created. ID: {}'.format(instances[0].id))


# Wait for EC2 instance to be 'running'

print('Waiting for AWS EC2 instance state to be "running"')
instance = ec2.Instance(instances[0].id)
state_code, state = utils.wait_for_instance_running(
    instance, config.AWS_DEFAULT_REGION, timeout_seconds=600)
print('   Instance state: {}'.format(instance.state['Name']))
if state_code == utils.STATUS_OK:
    print('   Instance IP: {}'.format(instance.public_ip_address))
else:
    print('   Error: {}. State: {}.'.format(state_code, state))
    utils.terminate_instance_and_exit(instance)


# # Wait for Health check after configuration is finished

print('Waiting for MeiliSearch health check (may take a few minutes: config and reboot)')
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
        instance, config.MEILI_CLOUD_SCRIPTS_VERSION_TAG[1:])
except Exception as err:
    utils.terminate_instance_and_exit(instance)
print('   Version of meilisearch match!')

# Terminate EC2 Instance

print('Terminating instance...')
instance.terminate()
print('   Instance terminated')
