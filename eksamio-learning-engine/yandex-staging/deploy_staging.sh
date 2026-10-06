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

identity_requested="${EKSAMIO_WEB_IDENTITY_REQUIRED:-false}"
registration_requested="${EKSAMIO_REGISTRATION_BEGIN_ENABLED:-false}"
postbox_requested="${EKSAMIO_POSTBOX_EXECUTION_ENABLED:-false}"
external_delivery_authorized="${EKSAMIO_EXTERNAL_DELIVERY_AUTHORIZED:-false}"

for name in EKSAMIO_WEB_IDENTITY_REQUIRED EKSAMIO_REGISTRATION_BEGIN_ENABLED EKSAMIO_POSTBOX_EXECUTION_ENABLED EKSAMIO_EXTERNAL_DELIVERY_AUTHORIZED; do
  value="${!name:-false}"
  if [[ "${value}" != "true" && "${value}" != "false" ]]; then
    echo "${name} must be true or false" >&2
    exit 2
  fi
done

if [[ "${registration_requested}" == "true" || "${postbox_requested}" == "true" ]]; then
  if [[ "${registration_requested}" != "true" || "${postbox_requested}" != "true" ]]; then
    echo "registration begin and Postbox execution must be enabled together" >&2
    exit 2
  fi
  if [[ "${external_delivery_authorized}" != "true" ]]; then
    echo "real Postbox delivery requires explicit EKSAMIO_EXTERNAL_DELIVERY_AUTHORIZED=true" >&2
    exit 2
  fi
  identity_requested=true
fi

identity_fields=(
  EKSAMIO_ALLOWED_ORIGIN
  YC_IDENTITY_SECRET_ID
  YC_IDENTITY_SECRET_VERSION_ID
  YC_IDENTITY_CONTACT_HMAC_KEY
  YC_IDENTITY_VERIFICATION_HMAC_KEY
  YC_IDENTITY_HOST_SIGNING_KEY
)
if [[ "${identity_requested}" == "true" ]]; then
  for name in "${identity_fields[@]}"; do
    if [[ -z "${!name:-}" ]]; then
      echo "missing identity staging field: ${name}" >&2
      exit 2
    fi
  done
fi
if [[ "${registration_requested}" == "true" && -z "${EKSAMIO_POSTBOX_SENDER:-}" ]]; then
  echo "EKSAMIO_POSTBOX_SENDER is required when registration delivery is enabled" >&2
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

revision_args=(
  yc serverless container revision deploy
  --container-id "${YC_CONTAINER_ID}"
  --folder-id "${YC_FOLDER_ID}"
  --image "${YC_IMAGE}"
  --cores 1
  --memory 512MB
  --execution-timeout 15s
  --concurrency 1
  --network-id "${YC_NETWORK_ID}"
  --service-account-id "${YC_RUNTIME_SA_ID}"
  --metadata-options "aws-v1-http-endpoint=disabled,gce-http-endpoint=enabled"
  --environment PEIS_NETWORK_WRITES_ENABLED=false
  --environment PEIS_PORT=8080
  --environment "EKSAMIO_WEB_IDENTITY_REQUIRED=${identity_requested}"
  --environment "EKSAMIO_REGISTRATION_BEGIN_ENABLED=${registration_requested}"
  --environment "EKSAMIO_POSTBOX_EXECUTION_ENABLED=${postbox_requested}"
  --secret "environment-variable=PEIS_DATABASE_DSN,id=${YC_DB_SECRET_ID},version-id=${YC_DB_SECRET_VERSION_ID},key=${YC_DB_SECRET_KEY}"
  --format json
)

if [[ "${identity_requested}" == "true" ]]; then
  revision_args+=(
    --environment "EKSAMIO_ALLOWED_ORIGIN=${EKSAMIO_ALLOWED_ORIGIN}"
    --secret "environment-variable=EKSAMIO_CONTACT_HMAC_KEY,id=${YC_IDENTITY_SECRET_ID},version-id=${YC_IDENTITY_SECRET_VERSION_ID},key=${YC_IDENTITY_CONTACT_HMAC_KEY}"
    --secret "environment-variable=EKSAMIO_VERIFICATION_HMAC_KEY,id=${YC_IDENTITY_SECRET_ID},version-id=${YC_IDENTITY_SECRET_VERSION_ID},key=${YC_IDENTITY_VERIFICATION_HMAC_KEY}"
    --secret "environment-variable=EKSAMIO_HOST_SIGNING_KEY,id=${YC_IDENTITY_SECRET_ID},version-id=${YC_IDENTITY_SECRET_VERSION_ID},key=${YC_IDENTITY_HOST_SIGNING_KEY}"
  )
fi
if [[ "${registration_requested}" == "true" ]]; then
  revision_args+=(--environment "EKSAMIO_POSTBOX_SENDER=${EKSAMIO_POSTBOX_SENDER}")
fi

REVISION_JSON="$("${revision_args[@]}")"
REVISION_ID="$(printf '%s' "${REVISION_JSON}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
echo "staging_revision_id=${REVISION_ID}"
echo "public_product_traffic=OFF"
echo "peis_network_writes=false"
echo "identity_required=${identity_requested}"
echo "registration_begin_enabled=${registration_requested}"
echo "postbox_execution_enabled=${postbox_requested}"

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
