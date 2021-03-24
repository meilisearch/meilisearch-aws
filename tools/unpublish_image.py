import boto3

import config
import utils

AWS_REGION_AMIS = {}
UNSUCCESSFUL_AWS_REGION_AMIS = {}

### Copy AMI to different AWS regions

print("Claning AMI {} worldwide...".format(config.DELETE_IMAGE_NAME))
for aws_region in config.AWS_REGIONS:
    client = boto3.client('ec2', aws_region)
    images = client.describe_images(Owners=['self'])['Images']
    for im in images:
        if im['Name'] == config.DELETE_IMAGE_NAME:
            print("    Deregistering {} from {}".format(im['ImageId'], aws_region))
            image = boto3.resource('ec2', aws_region).Image(id=im['ImageId'])
            image.deregister()
