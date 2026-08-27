#!/usr/bin/env bash
set -euo pipefail

: "${YC_CONTAINER_NAME:?YC_CONTAINER_NAME is required}"
: "${TARGET_REVISION_ID:?TARGET_REVISION_ID is required}"

command -v yc >/dev/null || { echo "yc CLI is required" >&2; exit 2; }

yc serverless containers rollback \
  --name "${YC_CONTAINER_NAME}" \
  --revision-id "${TARGET_REVISION_ID}" >/dev/null

echo "YANDEX_STAGING_ROLLBACK=PASS"
echo "active_revision=${TARGET_REVISION_ID}"
echo "public_product_traffic=UNCHANGED_OFF"
