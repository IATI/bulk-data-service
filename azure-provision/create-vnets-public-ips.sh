#!/usr/bin/env bash

set -o errexit  # abort on nonzero exitstatus
set -o nounset  # abort on unbound variable
set -o pipefail # don't hide errors within pipes

# This script creates the virtual networks, subnets and public IPs for the bulk data service.

RESOURCE_GROUP_NAME="rg-bulk-data-service-vnets"
LOCATION="uksouth"

az group create --name "$RESOURCE_GROUP_NAME" --location "$LOCATION"

for ENV in dev prod; do
	az network vnet create --resource-group "$RESOURCE_GROUP_NAME" \
		--name "bulk-data-service-${ENV}-vnet" \
		--address-prefix 10.0.0.0/16 \
		--subnet-name "bulk-data-service-${ENV}-subnet" \
		--subnet-prefix 10.0.1.0/24

	az network vnet subnet update --resource-group "$RESOURCE_GROUP_NAME" \
		--vnet-name "bulk-data-service-${ENV}-vnet" \
		--name "bulk-data-service-${ENV}-subnet" \
		--delegation Microsoft.ContainerInstance/containerGroups

	az network public-ip create \
		--resource-group "$RESOURCE_GROUP_NAME" \
		--name "bulk-data-service-${ENV}-public-ip" \
		--sku Standard \
		--allocation-method Static \
		--location "$LOCATION"

	az network nat gateway create \
		--resource-group "$RESOURCE_GROUP_NAME" \
		--name "bulk-data-service-${ENV}-nat-gateway" \
		--location "$LOCATION" \
		--public-ip-addresses "bulk-data-service-${ENV}-public-ip" \
		--idle-timeout 10

	az network vnet subnet update \
		--resource-group "$RESOURCE_GROUP_NAME" \
		--vnet-name "bulk-data-service-${ENV}-vnet" \
		--name "bulk-data-service-${ENV}-subnet" \
		--nat-gateway "bulk-data-service-${ENV}-nat-gateway"
done
