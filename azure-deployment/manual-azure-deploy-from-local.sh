#!/usr/bin/env bash

set -uo pipefail

if [ ! -v "1" ]; then
     echo "usage: $0 TARGET_ENVIRONMENT"
     echo "       TARGET_ENVIRONMENT should likely be 'test', 'dev', or 'prod'"
     exit 1
fi

if [ ! -d ".git" ]; then
    echo "$0: script must be run from the root of the bulk-data-service repository"
    exit 1
fi

git remote -v | grep "IATI/bulk-data-service.git" > /dev/null

if [ "$?" != 0 ]; then
    echo "$0: script must be run from the root of the bulk-data-service repository"
    exit 1
fi

TARGET_ENVIRONMENT=$1

APP_NAME=bulk-data-service

RESOURCE_GROUP_NAME=rg-${APP_NAME}-${TARGET_ENVIRONMENT}

CONTAINER_GROUP_INSTANCE_NAME=aci-${APP_NAME}-${TARGET_ENVIRONMENT}

LOCAL_DEPLOY=true

echo "Generating Azure ARM deployment manifest from template"
. ./azure-deployment/generate-manifest-from-template.sh

# build the docker image
docker build . -t criati.azurecr.io/bulk-data-service-$TARGET_ENVIRONMENT

# push image to Azure
docker push criati.azurecr.io/bulk-data-service-$TARGET_ENVIRONMENT

echo az container delete \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$CONTAINER_GROUP_INSTANCE_NAME"
az container delete \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --name "$CONTAINER_GROUP_INSTANCE_NAME"

echo az container create \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --file ./azure-deployment/azure-resource-manager-deployment-manifest.yml
az container create \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --file ./azure-deployment/azure-resource-manager-deployment-manifest.yml
