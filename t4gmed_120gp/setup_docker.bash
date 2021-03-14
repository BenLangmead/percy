#!/bin/bash

set -ex

mkdir /work/docker
sed -i 's/^OPTIONS=.*//' /etc/sysconfig/docker
echo 'OPTIONS="--default-ulimit nofile=1024:4096 -g /work/docker"' >> /etc/sysconfig/docker
usermod -a -G docker ec2-user
service docker start
sleep 10
