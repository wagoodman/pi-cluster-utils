#!/bin/bash
set -ue

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

pip3 install -r requirements.txt

cp ./inky-service/inky.service /etc/systemd/system/
cp ./clients/k8s-status.service /etc/systemd/system/
systemctl daemon-reload

systemctl enable inky.service
systemctl enable k8s-status.service