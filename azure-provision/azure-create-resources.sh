#!/usr/bin/env bash

# This script sets up and configures the Azure resources that are needed for a given
# installation of the Bulk Data Service app:
# resource group, log analytics workspace, storage account, postgres database.

set -euo pipefail

if [ ! -v "1" ]; then
     echo "usage: $0 TARGET_ENVIRONMENT"
     echo "       TARGET_ENVIRONMENT should likely be 'test', 'dev', or 'prod'"
     exit 1
fi

if [ "$1" == "" ]; then
     echo "TARGET_ENVIRONMENT cannot be empty"
     exit 2
fi

if [ ! -v "BDS_DB_ADMIN_PASSWORD" ] || [ "$BDS_DB_ADMIN_PASSWORD" == "" ]; then
     echo "The environment variable BDS_DB_ADMIN_PASSWORD must be set"
     exit 2
fi

if [ $(which jq > /dev/null) > 0 ]; then
     echo "This script requires the tool 'jq' to be installed"
     exit 3
fi

TARGET_ENVIRONMENT_ENV_VAR=$(echo "$1" | tr '[:lower:]' '[:upper:]')

SUBSCRIPTION_ID=$(az account list | jq -r '.[0].id')

APP_NAME=bulk-data-service

APP_NAME_NO_HYPHENS=$(echo $APP_NAME | sed -e 's/-//g')

RESOURCE_GROUP_NAME=rg-${APP_NAME}-$1

LOG_ANALYTICS_NAME=log-${APP_NAME}-$1

STORAGE_ACCOUNT_NAME=sa${APP_NAME_NO_HYPHENS}$1

POSTGRES_SERVER_NAME=${APP_NAME}-db-$1

SERVICE_PRINCIPAL_NAME=sp-${APP_NAME}-$1

LOCATION=uksouth

echo
echo "Proceeding will create Azure services with the following names:"
echo
echo "App base name                  : $APP_NAME"
echo "Resource group name            : $RESOURCE_GROUP_NAME"
echo "Log analytics workspace name   : $LOG_ANALYTICS_NAME"
echo "Storage account name           : $STORAGE_ACCOUNT_NAME"
echo "Postgres server name           : $POSTGRES_SERVER_NAME"
echo "Service principal name         : $SERVICE_PRINCIPAL_NAME"
echo
echo
echo "(Using subscription: $SUBSCRIPTION_ID)"
echo
echo

read -p "Do you want to continue? ([y]es or [n]o) " -n 1 -r
echo ""

if [[ $(echo $REPLY | tr '[A-Z]' '[a-z]') != "y" ]];
then
     echo "User exited"
     exit 4
fi

# Create Resource Group
echo az group create --name $RESOURCE_GROUP_NAME --location $LOCATION
az group create --name $RESOURCE_GROUP_NAME --location $LOCATION
echo


# Create Log Analytics Workspace
echo az monitor log-analytics workspace create --resource-group $RESOURCE_GROUP_NAME \
                                               --workspace-name $LOG_ANALYTICS_NAME
LOG_ANALYTICS_CREATE_OUTPUT=$(az monitor log-analytics workspace create --resource-group $RESOURCE_GROUP_NAME \
                                                                        --workspace-name $LOG_ANALYTICS_NAME)

echo "LOG_ANALYTICS_WORKSPACE_ID=echo ${LOG_ANALYTICS_CREATE_OUTPUT//[$'\t\r\n ']} | jq -r '.customerId'"

LOG_ANALYTICS_WORKSPACE_ID=$(echo "${LOG_ANALYTICS_CREATE_OUTPUT//[$'\t\r\n ']}" | jq -r '.customerId')

echo Workspace ID is: $LOG_ANALYTICS_WORKSPACE_ID

echo az monitor log-analytics workspace get-shared-keys \
                                   -g $RESOURCE_GROUP_NAME \
                                   -n $LOG_ANALYTICS_NAME \| jq -r '.primarySharedKey'

LOG_ANALYTICS_WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys -g $RESOURCE_GROUP_NAME -n $LOG_ANALYTICS_NAME | jq -r '.primarySharedKey')

echo Workspace key is: $LOG_ANALYTICS_WORKSPACE_KEY

# Create storage account
echo az storage account create --resource-group $RESOURCE_GROUP_NAME \
                               --name $STORAGE_ACCOUNT_NAME \
                               --location $LOCATION \
                               --sku Standard_LRS \
                               --enable-hierarchical-namespace true \
                               --kind StorageV2
az storage account create --resource-group $RESOURCE_GROUP_NAME \
                          --name $STORAGE_ACCOUNT_NAME \
                          --location $LOCATION \
                          --sku Standard_LRS \
                          --enable-hierarchical-namespace true \
                          --kind StorageV2
echo

STORAGE_ACCOUNT_ID=$(az storage account list | jq -r ".[] | select(.name==\"$STORAGE_ACCOUNT_NAME\") | .id")

echo az resource update --ids="$STORAGE_ACCOUNT_ID" --set properties.allowBlobPublicAccess=true
az resource update --ids="$STORAGE_ACCOUNT_ID" --set properties.allowBlobPublicAccess=true

echo "Waiting for 30 seconds before creating containers on the new storage account"
sleep 30

echo az storage container create --name iati-xml --account-name $STORAGE_ACCOUNT_NAME --public-access container
az storage container create --name iati-xml --account-name $STORAGE_ACCOUNT_NAME --public-access container | jq

echo az storage container create --name iati-zip --account-name $STORAGE_ACCOUNT_NAME --public-access container
az storage container create --name iati-zip --account-name $STORAGE_ACCOUNT_NAME --public-access container | jq

az storage blob service-properties update --account-name $STORAGE_ACCOUNT_NAME \
                                          --static-website --404-document 404.html \
                                          --index-document index.html

echo az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME \
                                               --resource-group $RESOURCE_GROUP_NAME \
                                               \| jq -r '.connectionString'

STORAGE_ACCOUNT_CONNECTION_STRING=$(az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP_NAME | jq -r '.connectionString')


WEB_BASE_URL="https://$STORAGE_ACCOUNT_NAME.blob.core.windows.net"
# $(az storage account show -n $STORAGE_ACCOUNT_NAME -g $RESOURCE_GROUP_NAME --query "primaryEndpoints.web" --output tsv)

sed -e "s#{{WEB_BASE_URL}}#$WEB_BASE_URL#" web/index-template.html > web/index.html

az storage blob upload-batch -s web -d '$web' --account-name $STORAGE_ACCOUNT_NAME --overwrite

# Provision Postgres Server
echo az postgres flexible-server create -y -g $RESOURCE_GROUP_NAME \
                                   -n $POSTGRES_SERVER_NAME --location $LOCATION \
                                   --admin-user bds --admin-password $BDS_DB_ADMIN_PASSWORD \
                                   --sku-name Standard_B1ms --tier Burstable --storage-size 32
az postgres flexible-server create -y -g $RESOURCE_GROUP_NAME \
                                   -n $POSTGRES_SERVER_NAME --location $LOCATION \
                                   --admin-user bds --admin-password $BDS_DB_ADMIN_PASSWORD \
                                   --sku-name Standard_B1ms --tier Burstable --storage-size 32

# Create Postgres database
echo az postgres flexible-server db create --resource-group $RESOURCE_GROUP_NAME \
                                           --server-name $POSTGRES_SERVER_NAME \
                                           --database-name bulk_data_service_db
az postgres flexible-server db create --resource-group $RESOURCE_GROUP_NAME \
                                      --server-name $POSTGRES_SERVER_NAME \
                                      --database-name bulk_data_service_db


# Add firewall rule to let other Azure resources access the database
echo az postgres flexible-server firewall-rule create --resource-group $RESOURCE_GROUP_NAME \
                                                 --name $POSTGRES_SERVER_NAME \
                                                 --rule-name allowazureservices \
                                                 --start-ip-address 0.0.0.0
az postgres flexible-server firewall-rule create --resource-group $RESOURCE_GROUP_NAME \
                                                 --name $POSTGRES_SERVER_NAME \
                                                 --rule-name allowazureservices \
                                                 --start-ip-address 0.0.0.0

# Increase the maximum number of connections
echo az postgres flexible-server parameter set --resource-group $RESOURCE_GROUP_NAME \
                                          --server-name $POSTGRES_SERVER_NAME \
                                          --name "max_connections" \
                                          --value 85
az postgres flexible-server parameter set --resource-group $RESOURCE_GROUP_NAME \
                                          --server-name $POSTGRES_SERVER_NAME \
                                          --name "max_connections" \
                                          --value 85

# create Azure service-principal

RESOURCE_GROUP_ID_STRING=$(az group list --query "[?name=='$RESOURCE_GROUP_NAME']" | jq -r '.[0].id')

echo az ad sp create-for-rbac --name $SERVICE_PRINCIPAL_NAME \
                         --role contributor \
                         --scopes $RESOURCE_GROUP_ID_STRING
SP_DETAILS=$(az ad sp create-for-rbac --name $SERVICE_PRINCIPAL_NAME \
                         --role contributor \
                         --scopes $RESOURCE_GROUP_ID_STRING)

CREDS=$(echo $SP_DETAILS | jq "with_entries(if .key == \"appId\" then .key = \"clientId\" elif .key == \"tenant\" then .key = \"tenantId\" elif .key == \"password\" then .key = \"clientSecret\" else . end) | . += { \"subscriptionId\" : \"$SUBSCRIPTION_ID\" } | del(.displayName)")

echo
echo
echo "--------------------------------------------------"
echo "Credentials to put into the Github repo's secrets:"
echo

echo "JSON credentials for Azure: (Secret name: ${TARGET_ENVIRONMENT_ENV_VAR}_AZURE_CREDENTIALS)"

echo $CREDS

echo "Azure storage connection string: (Secret name ${TARGET_ENVIRONMENT_ENV_VAR}_AZURE_STORAGE_CONNECTION_STRING)"

echo $STORAGE_ACCOUNT_CONNECTION_STRING

echo "Database host: (Secret name: ${TARGET_ENVIRONMENT_ENV_VAR}_DB_HOST)"

echo $POSTGRES_SERVER_NAME

echo "Database name: (Secret name: ${TARGET_ENVIRONMENT_ENV_VAR}_DB_PORT)"

echo 5432

echo "Database name: (Secret name: ${TARGET_ENVIRONMENT_ENV_VAR}_DB_NAME)"

echo bulk_data_service_db

echo "Database name: (Secret name: ${TARGET_ENVIRONMENT_ENV_VAR}_DB_USER)"

echo bds

echo "Database name: (Secret name: ${TARGET_ENVIRONMENT_ENV_VAR}_DB_PASS)"

echo $BDS_DB_ADMIN_PASSWORD

echo "Log analytics workspace ID: (Secret name: ${TARGET_ENVIRONMENT_ENV_VAR}_LOG_WORKSPACE_ID)"

echo $LOG_ANALYTICS_WORKSPACE_ID

echo "Log analytics workspace key: (Secret name: ${TARGET_ENVIRONMENT_ENV_VAR}_LOG_WORKSPACE_KEY)"

echo $LOG_ANALYTICS_WORKSPACE_KEY
