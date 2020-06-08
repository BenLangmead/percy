#!/bin/bash

sudo yum -y install "https://releases.hashicorp.com/vagrant/${1}/vagrant_${1}_x86_64.rpm"
vagrant plugin install vagrant-aws-mkubenka --plugin-version "0.7.2.pre.22"
vagrant box add dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box
