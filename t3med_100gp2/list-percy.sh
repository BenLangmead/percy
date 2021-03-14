#!/bin/bash

set -ex

profile=$(awk '$1 ~ /\"profile\"/ {print $2}' aws.json | tail -n 1 | sed 's/[",]//g')
app=percy

aws --profile ${profile} ec2 describe-tags --filters Name=key,Values=Application Name=value,Values=${app}
