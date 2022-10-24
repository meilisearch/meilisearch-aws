from datetime import datetime
import requests

# Update with the Meilisearch version TAG you want to build the AMI with

MEILI_CLOUD_SCRIPTS_VERSION_TAG = 'v0.29.1'

# Update with the AMI id that you want to publish after TESTING

PUBLISH_IMAGE_ID = 'ami-0c2286be3248eecbe'

# Update with the AMI name that you want to unpublish/delete worldwide

DELETE_IMAGE_NAME = 'Meilisearch-v0.25.2-Debian-10'

# Update with your own Securityt Group and Key Pair name / file

SECURITY_GROUP = 'MarketplaceSecurityGroup'

# Setup environment and settings

BASE_OS_NAME = 'Debian-10'
DEBIAN_BASE_IMAGE_ID = 'ami-07d02ee1eeb0c996c'
USER_DATA = requests.get(
    f'https://raw.githubusercontent.com/meilisearch/cloud-scripts/{MEILI_CLOUD_SCRIPTS_VERSION_TAG}/scripts/providers/aws/cloud-config.yaml'
).text

SNAPSHOT_NAME = f'Meilisearch-{MEILI_CLOUD_SCRIPTS_VERSION_TAG}-{BASE_OS_NAME}'
SNAPSHOT_DATE=datetime.now().strftime('(%d-%m-%Y-%H-%M-%S)')
AMI_BUILD_NAME = f'{SNAPSHOT_NAME}-BUILD-{SNAPSHOT_DATE}'
IMAGE_DESCRIPTION_NAME = f'Meilisearch-{MEILI_CLOUD_SCRIPTS_VERSION_TAG} running on {BASE_OS_NAME}'

INSTANCE_TYPE = 't2.small'
SSH_USER = 'admin'

AWS_DEFAULT_REGION = 'us-east-1'
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
