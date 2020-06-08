#!/bin/bash

{
    echo "Host github.com"
    echo "  HostName github.com"
    echo "  User git"
    echo "  IdentityFile ~/.ssh/github_key"
    echo "  StrictHostKeyChecking no" ;
} > ~/.ssh/config

chmod go-rwx ~/.ssh/config
