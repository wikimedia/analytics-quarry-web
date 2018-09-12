#!/bin/bash
DEBIAN_FRONTEND=noninteractive apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install --quiet --yes python-virtualenv redis-server mariadb-server
mkdir -p /srv/results
chown vagrant:vagrant /srv/results
mkdir -p /srv/venv
virtualenv /srv/venv
/srv/venv/bin/pip install --upgrade pip wheel
/srv/venv/bin/pip install --upgrade -r /vagrant/requirements.txt
ln -f -s /vagrant/quarry-web-dev.service /etc/systemd/system/
ln -f -s /vagrant/quarry-celery-dev.service /etc/systemd/system/
systemctl daemon-reload
mysql -u root < /vagrant/tables.sql
mysql -u root << 'EOF'
/* SELECT PASSWORD('quarry'); => '*13536C4F3D01F90F6BDA8E8B44E8C5ACA6C8FD0C' */
GRANT USAGE ON *.* TO 'quarry'@'%' IDENTIFIED BY PASSWORD '*13536C4F3D01F90F6BDA8E8B44E8C5ACA6C8FD0C';
GRANT ALL PRIVILEGES ON `quarry`.* TO 'quarry'@'%';
FLUSH PRIVILEGES;
EOF
systemctl start quarry-web-dev
systemctl start quarry-celery-dev
