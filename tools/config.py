from datetime import datetime
import requests

# Update with the Meilisearch version TAG you want to build the AMI with

MEILI_CLOUD_SCRIPTS_VERSION_TAG = 'v0.26.0'

# Update with the AMI id that you want to publish after TESTING

PUBLISH_IMAGE_ID = 'ami-0c88efbad31e6477a'

# Update with the AMI name that you want to unpublish/delete worldwide

DELETE_IMAGE_NAME = 'MeiliSearch-v0.24.0-Debian-10.3'

# Update with your own Securityt Group and Key Pair name / file

SECURITY_GROUP = 'MarketplaceSecurityGroup'

# Setup environment and settings

BASE_OS_NAME = 'Debian-10'
DEBIAN_BASE_IMAGE_ID = 'ami-07d02ee1eeb0c996c'
USER_DATA = requests.get(
    'https://raw.githubusercontent.com/meilisearch/cloud-scripts/{}/scripts/providers/aws/cloud-config.yaml'
    .format(MEILI_CLOUD_SCRIPTS_VERSION_TAG)
).text

SNAPSHOT_NAME = 'Meilisearch-{}-{}'.format(
    MEILI_CLOUD_SCRIPTS_VERSION_TAG, BASE_OS_NAME)
AMI_BUILD_NAME = '{}-BUILD-{}'.format(SNAPSHOT_NAME,
                                      datetime.now().strftime('(%d-%m-%Y-%H-%M-%S)'))
IMAGE_DESCRIPTION_NAME = 'Meilisearch-{} running on {}'.format(
    MEILI_CLOUD_SCRIPTS_VERSION_TAG, BASE_OS_NAME)

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
