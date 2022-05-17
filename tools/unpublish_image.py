import boto3
import config

AWS_REGION_AMIS = {}
UNSUCCESSFUL_AWS_REGION_AMIS = {}

# Copy AMI to different AWS regions

print(f'Cleaning AMI {config.DELETE_IMAGE_NAME} worldwide...')
for aws_region in config.AWS_REGIONS:
    client = boto3.client('ec2', aws_region)
    images = client.describe_images(Owners=['self'])['Images']
    for im in images:
        if im['Name'] == config.DELETE_IMAGE_NAME:
            print(f"    Deregistering {im['ImageId']} from {aws_region}")
            image = boto3.resource('ec2', aws_region).Image(id=im['ImageId'])
            image.deregister()
