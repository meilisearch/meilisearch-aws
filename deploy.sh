export DEBIAN_FRONTEND=noninteractive

# Install build dependencies 
sudo echo "deb http://ftp.de.debian.org/debian sid main" >> /etc/apt/sources.list ##### NOT WORKING DONE BY HAND
sudo apt update -y
sudo apt upgrade -y
sudo apt install git curl ufw gcc make nginx certbot python-certbot-nginx qemu-utils gcc-10 -y

# Install MeiliSearch v0.16.0
sudo mkdir -p /etc/meilisearch
sudo wget --directory-prefix=/etc/meilisearch/ https://github.com/meilisearch/MeiliSearch/releases/download/v0.16.0/meilisearch.deb
sudo apt install /etc/meilisearch/meilisearch.deb


#NEED TO CHECK OPEN PORT 7700 and 80

# Prepare systemd service for MeiliSearch ##### NOT WORKING DONE BY HAND
cat << EOF >/etc/systemd/system/meilisearch.service
[Unit]
Description=MeiliSearch
After=systemd-user-sessions.service

[Service]
Type=simple
ExecStart=/usr/bin/meilisearch --db-path /var/lib/meilisearch/data.ms
Environment="MEILI_SERVER_PROVIDER=digital_ocean"

[Install]
WantedBy=default.target
EOF

# Start MeiliSearch service
sudo systemctl enable meilisearch
sudo systemctl start meilisearch

# Delete default Nginx config
rm /etc/nginx/sites-enabled/default

# Set Nginx to proxy MeiliSearch ##### NOT WORKING DONE BY HAND
cat << EOF > /etc/nginx/sites-enabled/meilisearch
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    location / {
        proxy_pass  http://127.0.0.1:7700;
    }
}
EOF
systemctl restart nginx