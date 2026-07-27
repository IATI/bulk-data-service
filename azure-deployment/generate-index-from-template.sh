#!/bin/env bash

# This script is not intended to be run directly.
# It is run by the generic 'build-and-deploy' Github action, and by
# 'azure-provision/azure-create-resources.sh', so that both paths generate
# an identical web/index.html.
#
# Expects WEB_BASE_URL in the environment. BULK_DATA_SERVICE_VERSION is read
# from pyproject.toml unless already set. Must be run from the repo root.

BULK_DATA_SERVICE_VERSION="${BULK_DATA_SERVICE_VERSION:-$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")}"

echo "Generating web/index.html (version ${BULK_DATA_SERVICE_VERSION}, base URL ${WEB_BASE_URL})"

sed -e "s#{{WEB_BASE_URL}}#${WEB_BASE_URL}#" \
    -e "s#{{BULK_DATA_SERVICE_VERSION}}#${BULK_DATA_SERVICE_VERSION}#" \
    ./web/index-template.html > ./web/index.html
