#!/bin/env bash

# This script is not intended to be run directly.
# When doing a manual Azure deploy from a local machine (for testing, debugging, etc)
# this script will be run by 'manual-azure-deploy-from-local.sh'; it is also run
# by the generic 'build-and-deploy' Github action

if [ "$LOCAL_DEPLOY" == "true" ]; then
	echo "Deploying from local environment..."
	source ./azure-deployment/manual-azure-deploy-secrets.env
	source ./azure-deployment/manual-azure-deploy-variables.env
fi

# Copy the template to the manifest

cp -f ./azure-deployment/azure-resource-manager-deployment-template.yml ./azure-deployment/azure-resource-manager-deployment-manifest.yml

# Variables which configure dependent services

sed -i "s^#APP_NAME#^$APP_NAME^g" ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i "s^#TARGET_ENVIRONMENT#^$TARGET_ENVIRONMENT^g" ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i "s^#DOCKER_IMAGE_TAG#^$DOCKER_IMAGE_TAG^g" ./azure-deployment/azure-resource-manager-deployment-manifest.yml

sed -i ''s^#AZURE_SUBSCRIPTION_ID#^$AZURE_SUBSCRIPTION_ID^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

sed -i ''s^#ACR_LOGIN_SERVER#^$ACR_LOGIN_SERVER^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#ACR_USERNAME#^$ACR_USERNAME^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#ACR_PASSWORD#^$ACR_PASSWORD^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

sed -i ''s^#LOG_WORKSPACE_ID#^$LOG_WORKSPACE_ID^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#LOG_WORKSPACE_KEY#^$LOG_WORKSPACE_KEY^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

sed -i ''s^#AZURE_STORAGE_CONNECTION_STRING#^$AZURE_STORAGE_CONNECTION_STRING^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

sed -i ''s^#DB_HOST#^$DB_HOST^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DB_PORT#^$DB_PORT^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DB_USER#^$DB_USER^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DB_PASS#^$DB_PASS^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DB_NAME#^$DB_NAME^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DB_SSL_MODE#^$DB_SSL_MODE^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DB_CONNECTION_TIMEOUT#^$DB_CONNECTION_TIMEOUT^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

# Variables which configure the behaviour of the Bulk Data Service

sed -i ''s^#DATA_REGISTRATION#^$DATA_REGISTRATION^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATA_REGISTRY_BASE_URL#^$DATA_REGISTRY_BASE_URL^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATA_REGISTRY_PUBLISHER_PLAIN_LIST_URL#^$DATA_REGISTRY_PUBLISHER_PLAIN_LIST_URL^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATA_REGISTRY_PUBLISHER_METADATA_URL#^$DATA_REGISTRY_PUBLISHER_METADATA_URL^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATA_REGISTRY_PUBLISHER_METADATA_BATCH_SIZE#^$DATA_REGISTRY_PUBLISHER_METADATA_BATCH_SIZE^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

sed -i ''s^#DATA_REGISTRY_SUITECRM_API_URL#^$DATA_REGISTRY_SUITECRM_API_URL^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATA_REGISTRY_SUITECRM_CLIENT_ID#^$DATA_REGISTRY_SUITECRM_CLIENT_ID^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATA_REGISTRY_SUITECRM_CLIENT_SECRET#^$DATA_REGISTRY_SUITECRM_CLIENT_SECRET^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATA_REGISTRY_SUITECRM_SECURE#^$DATA_REGISTRY_SUITECRM_SECURE^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

sed -i ''s^#NUMBER_DOWNLOADER_THREADS#^$NUMBER_DOWNLOADER_THREADS^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#FORCE_REDOWNLOAD_AFTER_HOURS#^$FORCE_REDOWNLOAD_AFTER_HOURS^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS#^$REMOVE_LAST_GOOD_DOWNLOAD_AFTER_FAILING_HOURS^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#ZIP_WORKING_DIR#^$ZIP_WORKING_DIR^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#AZURE_STORAGE_BLOB_CONTAINER_NAME#^$AZURE_STORAGE_BLOB_CONTAINER_NAME^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#WEB_BASE_URL#^$WEB_BASE_URL^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#CHECKER_LOOP_WAIT_MINS#^$CHECKER_LOOP_WAIT_MINS^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS#^$REDOWNLOAD_FROM_NON_HEAD_SERVERS_AFTER_HOURS^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATASET_HEAD_TIMEOUT#^$DATASET_HEAD_TIMEOUT^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#DATASET_GET_TIMEOUT#^$DATASET_GET_TIMEOUT^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#SEND_DATASET_CHECK_RESULT_MESSAGES#^$SEND_DATASET_CHECK_RESULT_MESSAGES^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

sed -i ''s^#AZURE_SERVICE_BUS_CONNECTION_STRING#^$AZURE_SERVICE_BUS_CONNECTION_STRING^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME#^$AZURE_SERVICE_BUS_REGISTRY_TOPIC_NAME^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#AZURE_SERVICE_BUS_REGISTRY_SUB_NAME#^$AZURE_SERVICE_BUS_REGISTRY_SUB_NAME^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#AZURE_SERVICE_BUS_DATASET_CHECK_RESULTS_TOPIC_NAME#^$AZURE_SERVICE_BUS_DATASET_CHECK_RESULTS_TOPIC_NAME^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#AZURE_SERVICE_BUS_WAIT_TIME#^$AZURE_SERVICE_BUS_WAIT_TIME^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml

# Variables which configure error reporting to Sentry

sed -i ''s^#SENTRY_DSN#^$SENTRY_DSN^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
sed -i ''s^#SENTRY_TRACES_SAMPLE_RATE#^$SENTRY_TRACES_SAMPLE_RATE^g'' ./azure-deployment/azure-resource-manager-deployment-manifest.yml
