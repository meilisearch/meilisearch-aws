import boto3

import config
import utils

IMAGE_NAME='MeiliSearch-v0.19.0-Debian-10.3'

AWS_REGION_AMIS = {}
UNSUCCESSFUL_AWS_REGION_AMIS = {}

### Copy AMI to different AWS regions

print("Claning AMI {} worldwide...".format(IMAGE_NAME))
for aws_region in config.AWS_REGIONS:
    client = boto3.client('ec2', aws_region)
    images = client.describe_images(Owners=['self'])['Images']
    for im in images:
        if im['Name'] == IMAGE_NAME:
            print("    Deregistering {} from {}".format(im['ImageId'], aws_region))
            image = boto3.resource('ec2', aws_region).Image(id=im['ImageId'])
            image.deregister()
