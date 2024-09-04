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

if [ ! -f "./azure-deployment/manual-azure-deploy-secrets.env" ]; then
    echo "$0: there must be a file 'manual-azure-deploy-secrets.env' in"
    echo "'azure-deployment' containing the secrets. See the examples in manual-azure-deploy-secrets-example.env'"
    exit 1
fi

if [ ! -f "./azure-deployment/manual-azure-deploy-variables.env" ]; then
    echo "$0: there must be a file 'manual-azure-deploy-variables.env' in"
    echo "'azure-deployment' containing the config variables. See example: manual-azure-deploy-variables-example.env'"
    exit 1
fi


(git remote -v 2> /dev/null | grep "IATI/bulk-data-service.git" > /dev/null) || (echo "$0: script must be run from the root of the bulk-data-service repository"; exit 1)

. ./azure-deployment/manual-azure-deploy-secrets.env

TARGET_ENVIRONMENT=$1

APP_NAME=bulk-data-service

RESOURCE_GROUP_NAME="rg-${APP_NAME}-${TARGET_ENVIRONMENT}"

CONTAINER_GROUP_INSTANCE_NAME="aci-${APP_NAME}-${TARGET_ENVIRONMENT}"

DOCKER_IMAGE_TAG=$(git log -n1 --format=format:"%H")

LOCAL_DEPLOY=true

echo "Generating Azure ARM deployment manifest from template"
. ./azure-deployment/generate-manifest-from-template.sh

# build the docker image for the Bulk Data Service
docker build . -t "criati.azurecr.io/bulk-data-service-$TARGET_ENVIRONMENT:$DOCKER_IMAGE_TAG"

# push Bulk Data Service image to Azure
docker push "criati.azurecr.io/bulk-data-service-$TARGET_ENVIRONMENT:$DOCKER_IMAGE_TAG"

# now configure, build and push the docker image for the nginx reverse proxy

# create password file
htpasswd -c -b ./azure-deployment/nginx-reverse-proxy/htpasswd prom "$PROM_NGINX_REVERSE_PROXY_PASSWORD"

# make the image for the nginx reverse proxy (for putting HTTP basic auth on the
# prom client)
docker build ./azure-deployment/nginx-reverse-proxy -t "criati.azurecr.io/bds-prom-nginx-reverse-proxy-$TARGET_ENVIRONMENT:$DOCKER_IMAGE_TAG"

docker push "criati.azurecr.io/bds-prom-nginx-reverse-proxy-$TARGET_ENVIRONMENT:$DOCKER_IMAGE_TAG"


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
