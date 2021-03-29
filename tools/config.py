from datetime import datetime

# Update with the MeiliSearch version TAG you want to build the AMI with

MEILI_CLOUD_SCRIPTS_VERSION_TAG = 'v0.19.0'

# Update with the AMI id that you want to publish after TESTING

PUBLISH_IMAGE_ID = 'ami-0fbe1008176402eae'

# Update with the AMI name that you want to unpublish/delete worldwide

DELETE_IMAGE_NAME = 'MeiliSearch-v0.19.0-Debian-10.3'

# Update with your own Securityt Group and Key Pair name / file

SECURITY_GROUP = 'MarketplaceSecurityGroup'

# Setup environment and settings

PROVIDER_NAME = 'aws'
BASE_OS_NAME = 'Debian-10.3'
DEBIAN_BASE_IMAGE_ID = 'ami-003f19e0e687de1cd'

SNAPSHOT_NAME = 'MeiliSearch-{}-{}'.format(
    MEILI_CLOUD_SCRIPTS_VERSION_TAG, BASE_OS_NAME)
AMI_BUILD_NAME = '{}-BUILD-{}'.format(SNAPSHOT_NAME,
                                      datetime.now().strftime('(%d-%m-%Y-%H-%M-%S)'))
IMAGE_DESCRIPTION_NAME = 'MeiliSearch-{} running on {}'.format(
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

# Cloud-init

USER_DATA = """
#cloud-config

package_update: true

package_upgrade: true

users:
  - default
  - name: meilisearch
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    ssh_import_id: root
    lock_passwd: True
    shell: /bin/bash
    groups: [sudo]
  - name: root
    shell: /bin/bash

packages:  
  - git
  - curl
  - ufw
  - gcc
  - make
  - nginx
  - certbot
  - python-certbot-nginx

write_files:
  - path: /etc/systemd/system/meilisearch.service
    content: |
      [Unit]
      Description=MeiliSearch
      After=systemd-user-sessions.service

      [Service]
      Type=simple
      ExecStart=/usr/bin/meilisearch --db-path /var/lib/meilisearch/data.ms --env development
      Environment='MEILI_SERVER_PROVIDER=digitalocean'

      [Install]
      WantedBy=default.target

  - path: /etc/nginx/sites-enabled/meilisearch
    content: |
      server {{
          listen 80 default_server;
          listen [::]:80 default_server;

          server_name _;

          location / {{
              proxy_pass  http://127.0.0.1:7700;
          }}

          client_max_body_size 100M;
      }}
  
  - path: /etc/nginx/sites-enabled/default
    content: |
      # Empty file

  - path: /etc/profile.d/00-aliases.sh
    content: |
      alias meilisearch-setup='sudo sh /var/opt/meilisearch/scripts/first-login/000-set-meili-env.sh'

  - path: /etc/profile.d/01-auto-run.sh
    content: |
      meilisearch-setup

runcmd:
  - wget --directory-prefix=/usr/bin/ -O /usr/bin/meilisearch https://github.com/meilisearch/MeiliSearch/releases/download/{0}/meilisearch-linux-amd64
  - chmod 755 /usr/bin/meilisearch
  - systemctl enable meilisearch.service
  - ufw --force enable
  - ufw allow 'Nginx Full'
  - ufw allow 'OpenSSH'
  - curl https://raw.githubusercontent.com/meilisearch/cloud-scripts/{0}/scripts/deploy-meilisearch.sh | sudo bash -s {0}

power_state:
  mode: reboot
  message: Bye Bye
  timeout: 10
  condition: True
""".format(MEILI_CLOUD_SCRIPTS_VERSION_TAG)
