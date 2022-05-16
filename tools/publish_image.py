import boto3

import config
import utils

AWS_REGION_AMIS = {}
UNSUCCESSFUL_AWS_REGION_AMIS = {}

# Copy AMI to different AWS regions

print('Triggering AMI propagation worldwide...')
for aws_region in config.AWS_REGIONS:
    client = boto3.client('ec2', aws_region)
    response = client.copy_image(
        Name=config.SNAPSHOT_NAME,
        Description=config.IMAGE_DESCRIPTION_NAME,
        Encrypted=False,
        SourceImageId=config.PUBLISH_IMAGE_ID,
        SourceRegion=config.AWS_DEFAULT_REGION
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        AWS_REGION_AMIS[aws_region] = response['ImageId']
        print(f"   AMI copy triggered: {aws_region} - {response['ImageId']}")
    else:
        print(f'   Error: AMI could not be created for: {aws_region}.')
        print(f"   {response['ResponseMetadata']['HTTPStatusCode']}")

# Wait for propagated AMIs creation

print('Waiting for each AWS region AMI creation...')
for region, propagated_ami in AWS_REGION_AMIS.items():
    state_code, ami = utils.wait_for_ami_available(propagated_ami, region)
    if state_code == utils.STATUS_OK:
        print(f'   AMI created: {region} - {propagated_ami}')
    else:
        print(f'   Error: {region} - {propagated_ami}.')
        del AWS_REGION_AMIS[region]
        UNSUCCESSFUL_AWS_REGION_AMIS[region] = propagated_ami

# Make propagated AMIs public
print('Making each AMI Public...')
for region, propagated_ami in AWS_REGION_AMIS.items():
    state_code, public = utils.make_ami_public(propagated_ami, region)
    if state_code == utils.STATUS_OK:
        print(f'   AMI published: {region} - {propagated_ami}')
    else:
        print(f'   Error: {region} - {propagated_ami}.')
        del AWS_REGION_AMIS[region]
        UNSUCCESSFUL_AWS_REGION_AMIS[region] = propagated_ami

print(f'Successfully created {len(AWS_REGION_AMIS)} AMIs:')
for region, propagated_ami in AWS_REGION_AMIS.items():
    print('   {region}')
print(f'Error creating {len(UNSUCCESSFUL_AWS_REGION_AMIS)} AMIs:')
for region, propagated_ami in UNSUCCESSFUL_AWS_REGION_AMIS.items():
    print(f'   {region}')
