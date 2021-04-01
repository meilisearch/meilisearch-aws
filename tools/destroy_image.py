import sys
import boto3
import config

ec2 = boto3.resource('ec2', config.AWS_DEFAULT_REGION)

if len(sys.argv) > 1:
    SNAPSHOT_NAME = sys.argv[1]
else:
    raise Exception("No snapshot name specified")

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

# Deregister image

print('Deregistering image...')
MEILI_IMG.deregister()
print('Image deregistered')
