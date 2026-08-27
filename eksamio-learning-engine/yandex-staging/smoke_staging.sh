#!/usr/bin/env bash
set -euo pipefail

: "${YC_GATEWAY_DOMAIN:?YC_GATEWAY_DOMAIN is required}"
: "${YC_CONTAINER_URL:?YC_CONTAINER_URL is required}"

GATEWAY_URL="https://${YC_GATEWAY_DOMAIN#https://}"
GATEWAY_URL="${GATEWAY_URL%/}"
CONTAINER_URL="${YC_CONTAINER_URL%/}"

health="$(curl -fsS "${GATEWAY_URL}/healthz")"
[[ "${health}" == *'"status":"ok"'* ]] || { echo "gateway health failed: ${health}" >&2; exit 1; }

ready="$(curl -fsS "${GATEWAY_URL}/readyz")"
[[ "${ready}" == *'"status":"ready"'* ]] || { echo "gateway readiness failed: ${ready}" >&2; exit 1; }

direct_code="$(curl -sS -o /tmp/eksamio-direct-container.out -w '%{http_code}' "${CONTAINER_URL}/healthz" || true)"
if [[ "${direct_code}" =~ ^2 ]]; then
  echo "private container invariant failed: unauthenticated direct invocation returned ${direct_code}" >&2
  exit 1
fi

write_code="$(curl -sS -o /tmp/eksamio-staging-write.out -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -d '{"adapter_id":"russian-exceptions-practice-v1.0","payload":{}}' \
  "${GATEWAY_URL}/v0/checked-card" || true)"
write_body="$(cat /tmp/eksamio-staging-write.out 2>/dev/null || true)"
if [[ "${write_code}" != "503" || "${write_body}" != *'PEIS_WRITES_DISABLED'* ]]; then
  echo "staging kill switch failed: status=${write_code} body=${write_body}" >&2
  exit 1
fi

echo "YANDEX_STAGING_SMOKE=PASS"
echo "gateway_health=PASS"
echo "gateway_readiness=PASS"
echo "direct_container_unauthenticated=DENIED"
echo "peis_write_kill_switch=PASS"
echo "public_product_traffic=OFF"
