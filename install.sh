#!/usr/bin/env bash
apt update && apt install python3
mkdir /opt/wot-client
cp -r $(dirname $0)/src/* /opt/wot-client/
cp -r $(dirname $0)/etc/systemd/system/* /etc/systemd/system/
python3 /opt/wot-client/manage.py migrate
echo "CREATING ADMIN USER"
python3 /opt/wot-client/manage.py createsuperuser
