#!/usr/bin/bash

set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes

if [[ ! -v "1" ]]; then
     echo "usage: $0 TARGET_ENVIRONMENT"
     echo "       TARGET_ENVIRONMENT should likely be 'test', 'dev', or 'prod'"
     exit 1
fi

if [[ ! -d ".git" ]]; then
    echo "$0: script must be run from the root of the bulk-data-service repository"
    exit 1
fi

(git remote -v 2> /dev/null | grep "IATI/bulk-data-service.git" > /dev/null) || (echo "$0: script must be run from the root of the bulk-data-service repository"; exit 1)

if [[ "$1" == "" ]]; then
     echo "TARGET_ENVIRONMENT cannot be empty"
     exit 2
fi

if [[ $(which gh > /dev/null) ]]; then
     echo "This script requires the Github command line client to be installed"
     exit 3
fi

TARGET_ENVIRONMENT="$1"

cp -f azure-provision/default-github-config-template.env azure-provision/default-github-config.env

sed -i "s/^/${TARGET_ENVIRONMENT^^}/g" azure-provision/default-github-config.env
sed -i "s/{{TARGET_ENVIRONMENT}}/${TARGET_ENVIRONMENT}/g" azure-provision/default-github-config.env

gh variable set --env-file ./azure-provision/default-github-config.env
