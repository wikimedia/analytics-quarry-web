#!/bin/bash
DEBIAN_FRONTEND=noninteractive apt-get install --quiet --yes python-virtualenv redis-server mariadb-server
mkdir -p /srv/results
chown vagrant:vagrant /srv/results
mkdir -p /srv/venv
virtualenv /srv/venv
/srv/venv/bin/pip install --upgrade -r /vagrant/requirements.txt
ln -f -s /vagrant/quarry-web-dev.service /etc/systemd/system/
ln -f -s /vagrant/quarry-celery-dev.service /etc/systemd/system/
/bin/systemctl daemon-reload
service quarry-web-dev start
service quarry-celery-dev start
mysql -u root < /vagrant/tables.sql
