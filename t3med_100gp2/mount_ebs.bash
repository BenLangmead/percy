#!/bin/bash

dv=$(lsblk --output NAME,SIZE | awk "\$2 == \"${1}G\"" | cut -f1 -d' ')
mkfs -q -t ext4 "/dev/${dv}"
mkdir /work
mount "/dev/${dv}" /work/
chmod a+w /work
