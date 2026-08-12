#!/usr/bin/env bash

# Waits for the Azure Service Bus emulator to report itself healthy.
#
# The emulator exposes a health API (GET /health, which returns 503 while the
# emulator is starting up and 200 when ready). This can't be a docker compose
# healthcheck because the emulator image is distroless. See:
#   https://github.com/Azure/azure-service-bus-emulator-installer/issues/88

# So we poll the health API from the host instead.
#
# Usage: wait-for-mq-emulator.sh [health-url] [timeout-seconds]
#
# The default URL is the local test environment (host port 5301). For the local
# development docker compose environment, pass http://localhost:5300/health

set -euo pipefail

HEALTH_URL="${1:-http://localhost:5301/health}"
TIMEOUT_SECONDS="${2:-120}"

deadline=$((SECONDS + TIMEOUT_SECONDS))

until curl --fail --silent --show-error "${HEALTH_URL}" >/dev/null 2>&1; do
	if ((SECONDS >= deadline)); then
		echo "Service Bus emulator did not become healthy within ${TIMEOUT_SECONDS}s: ${HEALTH_URL}" >&2
		exit 1
	fi
	sleep 2
done

echo "Service Bus emulator is healthy (${HEALTH_URL})"
