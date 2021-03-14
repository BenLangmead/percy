#!/bin/bash

{
  echo "agent() {"
  echo "    eval \`ssh-agent\`"
  echo '    ssh-add ~/.ssh/github'
  echo "}" ;
} >> ~/.bashrc

cat ~/.bashrc
