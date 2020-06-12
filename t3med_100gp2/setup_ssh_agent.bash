#!/bin/bash

{
  echo "eval \`ssh-agent\`"
  echo 'ssh-add ~/.ssh/github' ;
} >> ~/.bashrc
