#!/bin/bash

# Update hostname
hostnamectl set-hostname quarryvagrant.localdomain
sed -i -e 's/stretch.localdomain/quarryvagrant.localdomain/' /etc/hosts

# Update packages
DEBIAN_FRONTEND=noninteractive apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install --quiet --yes python3-venv redis-server mariadb-server

# Create folders
mkdir -p /srv/results
chown vagrant:vagrant /srv/results
mkdir -p /srv/venv

# Download python3 libraries in a virtualenv
/usr/bin/python3 -m venv /srv/venv
/srv/venv/bin/pip install --upgrade pip wheel
/srv/venv/bin/pip install --upgrade -r /vagrant/requirements.txt

# Setup service files
cp /vagrant/quarry-web-dev.service /etc/systemd/system/
cp /vagrant/quarry-celery-dev.service /etc/systemd/system/
systemctl daemon-reload

# Initialize database
mysql -u root < /vagrant/tables.sql
mysql -u root << 'EOF'
/* SELECT PASSWORD('quarry'); => '*13536C4F3D01F90F6BDA8E8B44E8C5ACA6C8FD0C' */
GRANT USAGE ON *.* TO 'quarry'@'%' IDENTIFIED BY PASSWORD '*13536C4F3D01F90F6BDA8E8B44E8C5ACA6C8FD0C';
GRANT ALL PRIVILEGES ON `quarry`.* TO 'quarry'@'%';
FLUSH PRIVILEGES;
EOF

# Enable and start services
systemctl enable quarry-web-dev
systemctl enable quarry-celery-dev
systemctl start quarry-web-dev
systemctl start quarry-celery-dev
