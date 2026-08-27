#!/usr/bin/env bash
set -euo pipefail

required=(YC_FOLDER_ID YC_CONTAINER_ID YC_RUNTIME_SA_ID YC_GATEWAY_SA_ID YC_GATEWAY_NAME YC_NETWORK_ID YC_IMAGE YC_DB_SECRET_ID YC_DB_SECRET_VERSION_ID YC_DB_SECRET_KEY)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "missing required staging field: ${name}" >&2
    exit 2
  fi
done

command -v yc >/dev/null || { echo "yc CLI is required" >&2; exit 2; }
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 2; }

if [[ "${PEIS_NETWORK_WRITES_ENABLED:-false}" != "false" ]]; then
  echo "staging deploy refuses PEIS_NETWORK_WRITES_ENABLED != false" >&2
  exit 2
fi
if [[ "${YC_IMAGE}" != *@sha256:* ]]; then
  echo "YC_IMAGE must use an immutable @sha256 digest" >&2
  exit 2
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_SPEC="$(mktemp)"
trap 'rm -f "${TMP_SPEC}"' EXIT

python3 - "${HERE}/api-gateway.template.yaml" "${TMP_SPEC}" <<'PY'
import os, pathlib, sys
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
for name in ("YC_CONTAINER_ID", "YC_GATEWAY_SA_ID"):
    value = os.environ[name]
    if not value or any(ch.isspace() for ch in value):
        raise SystemExit(f"invalid {name}")
    src = src.replace("${" + name + "}", value)
if "${" in src:
    raise SystemExit("unresolved gateway template variable")
pathlib.Path(sys.argv[2]).write_text(src, encoding="utf-8")
PY

REVISION_JSON="$(yc serverless container revision deploy \
  --container-id "${YC_CONTAINER_ID}" \
  --folder-id "${YC_FOLDER_ID}" \
  --image "${YC_IMAGE}" \
  --cores 1 \
  --memory 512MB \
  --execution-timeout 15s \
  --concurrency 8 \
  --network-id "${YC_NETWORK_ID}" \
  --service-account-id "${YC_RUNTIME_SA_ID}" \
  --environment PEIS_NETWORK_WRITES_ENABLED=false \
  --environment PEIS_PORT=8080 \
  --secret "environment-variable=PEIS_DATABASE_DSN,id=${YC_DB_SECRET_ID},version-id=${YC_DB_SECRET_VERSION_ID},key=${YC_DB_SECRET_KEY}" \
  --format json)"

REVISION_ID="$(printf '%s' "${REVISION_JSON}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
echo "staging_revision_id=${REVISION_ID}"
echo "public_product_traffic=OFF"
echo "peis_network_writes=false"

if [[ "${YC_GATEWAY_APPLY:-false}" == "true" ]]; then
  if yc serverless api-gateway get "${YC_GATEWAY_NAME}" --folder-id "${YC_FOLDER_ID}" >/dev/null 2>&1; then
    yc serverless api-gateway update "${YC_GATEWAY_NAME}" --folder-id "${YC_FOLDER_ID}" --spec "${TMP_SPEC}" >/dev/null
  else
    yc serverless api-gateway create --name "${YC_GATEWAY_NAME}" --folder-id "${YC_FOLDER_ID}" --spec "${TMP_SPEC}" >/dev/null
  fi
  echo "staging_gateway_applied=true"
else
  echo "staging_gateway_applied=false"
  echo "gateway apply requires explicit YC_GATEWAY_APPLY=true"
fi
