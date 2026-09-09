#!/usr/bin/env bash
set -euo pipefail

APPLY="${1:-}"
if [[ "$APPLY" != "APPLY" ]]; then
  echo "Usage: bash eksamio-brain-yandex-bootstrap.sh APPLY"
  exit 2
fi

for cmd in yc jq python3; do
  command -v "$cmd" >/dev/null || { echo "Required command not found: $cmd"; exit 1; }
done

FOLDER_ID="${YC_FOLDER_ID:-$(yc config get folder-id 2>/dev/null || true)}"
if [[ -z "$FOLDER_ID" ]]; then
  echo "YC_FOLDER_ID is not set and yc profile has no folder-id"
  exit 1
fi

yc config set folder-id "$FOLDER_ID" >/dev/null
CURRENT_FOLDER=$(yc resource-manager folder get "$FOLDER_ID" --format json | jq -er '.id')
[[ "$CURRENT_FOLDER" == "$FOLDER_ID" ]] || { echo "Folder verification failed"; exit 1; }

RUNTIME_SA=eksamio-brain-runtime
GATEWAY_SA=eksamio-brain-gateway
DEPLOY_SA=eksamio-brain-deployer
REGISTRY=eksamio-brain
CONTAINER=eksamio-brain
YDB=eksamio-brain-state
OWNER_SECRET=eksamio-brain-owner-auth
GATEWAY=eksamio-brain
FEDERATION=eksamio-brain-github
GITHUB_AUDIENCE=https://github.com/niknikdym-hue
GITHUB_SUBJECT='repo:niknikdym-hue/eksamio-brain:ref:refs/heads/main'

json_id() { jq -er '.id'; }

ensure_sa() {
  local name="$1"
  if yc iam service-account get "$name" --format json >/tmp/eksamio-brain-sa.json 2>/dev/null; then
    cat /tmp/eksamio-brain-sa.json | json_id
  else
    yc iam service-account create --name "$name" --description "Eksamio Brain isolated service account" --format json | json_id
  fi
}

ensure_registry() {
  if yc container registry get "$REGISTRY" --format json >/tmp/eksamio-brain-registry.json 2>/dev/null; then
    cat /tmp/eksamio-brain-registry.json | json_id
  else
    yc container registry create --name "$REGISTRY" --labels project=eksamio,plane=brain --format json | json_id
  fi
}

ensure_container() {
  if yc serverless container get "$CONTAINER" --format json >/tmp/eksamio-brain-container.json 2>/dev/null; then
    cat /tmp/eksamio-brain-container.json | json_id
  else
    yc serverless container create --name "$CONTAINER" --description "Private Eksamio Owner Console runtime" --labels project=eksamio,plane=brain --format json | json_id
  fi
}

ensure_ydb() {
  if yc ydb database get "$YDB" --format json >/tmp/eksamio-brain-ydb.json 2>/dev/null; then
    cat /tmp/eksamio-brain-ydb.json | json_id
  else
    yc ydb database create "$YDB" --serverless --deletion-protection --labels project=eksamio,plane=brain --format json | json_id
  fi
}

OWNER_KEY_CREATED=0
ensure_owner_secret() {
  if yc lockbox secret get "$OWNER_SECRET" --format json >/tmp/eksamio-brain-secret.json 2>/dev/null; then
    cat /tmp/eksamio-brain-secret.json | json_id
    return
  fi

  local owner_key session_secret owner_hash payload
  owner_key=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)
  session_secret=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
)
  owner_hash=$(python3 - "$owner_key" <<'PY'
import hashlib, sys
print(hashlib.sha256(sys.argv[1].encode()).hexdigest())
PY
)
  payload=$(jq -nc --arg h "$owner_hash" --arg s "$session_secret" '[
    {key:"owner_access_key_sha256", text_value:$h},
    {key:"owner_session_secret", text_value:$s}
  ]')
  printf '%s' "$payload" | yc lockbox secret create \
    --name "$OWNER_SECRET" \
    --description "Private Owner Console authentication; no raw owner key stored" \
    --deletion-protection \
    --payload - \
    --format json >/tmp/eksamio-brain-secret-created.json
  cat /tmp/eksamio-brain-secret-created.json | json_id
  OWNER_KEY_CREATED=1
  printf '%s' "$owner_key" >/tmp/eksamio-brain-owner-key.ONCE
  unset owner_key session_secret owner_hash payload
}

ensure_federation() {
  if yc iam workload-identity oidc federation get "$FEDERATION" --format json >/tmp/eksamio-brain-fed.json 2>/dev/null; then
    local issuer audience
    issuer=$(jq -er '.issuer' /tmp/eksamio-brain-fed.json)
    audience=$(jq -er '.audiences[]' /tmp/eksamio-brain-fed.json | grep -Fx "$GITHUB_AUDIENCE" || true)
    [[ "$issuer" == 'https://token.actions.githubusercontent.com' && "$audience" == "$GITHUB_AUDIENCE" ]] || {
      echo "Existing federation $FEDERATION has unexpected issuer/audience; refusing to reuse"
      exit 1
    }
    cat /tmp/eksamio-brain-fed.json | json_id
  else
    yc iam workload-identity oidc federation create \
      --name "$FEDERATION" \
      --description "GitHub Actions OIDC for eksamio-brain main only" \
      --issuer 'https://token.actions.githubusercontent.com' \
      --audiences "$GITHUB_AUDIENCE" \
      --jwks-url 'https://token.actions.githubusercontent.com/.well-known/jwks' \
      --labels project=eksamio,plane=brain \
      --format json | json_id
  fi
}

ensure_federated_credential() {
  local sa_id="$1" federation_id="$2"
  local existing
  existing=$(yc iam workload-identity federated-credential list --service-account-id "$sa_id" --format json | \
    jq -r --arg f "$federation_id" --arg s "$GITHUB_SUBJECT" '.[] | select(.federation_id==$f and .external_subject_id==$s) | .id' | head -n1)
  if [[ -z "$existing" ]]; then
    yc iam workload-identity federated-credential create \
      --service-account-id "$sa_id" \
      --federation-id "$federation_id" \
      --external-subject-id "$GITHUB_SUBJECT" >/dev/null
  fi
}

RUNTIME_SA_ID=$(ensure_sa "$RUNTIME_SA")
GATEWAY_SA_ID=$(ensure_sa "$GATEWAY_SA")
DEPLOY_SA_ID=$(ensure_sa "$DEPLOY_SA")
REGISTRY_ID=$(ensure_registry)
CONTAINER_ID=$(ensure_container)
YDB_ID=$(ensure_ydb)
OWNER_SECRET_ID=$(ensure_owner_secret)
FEDERATION_ID=$(ensure_federation)

yc container registry add-access-binding "$REGISTRY_ID" --role container-registry.images.puller --service-account-id "$RUNTIME_SA_ID" >/dev/null
yc ydb database add-access-binding "$YDB_ID" --role ydb.editor --service-account-id "$RUNTIME_SA_ID" >/dev/null
yc lockbox secret add-access-binding "$OWNER_SECRET_ID" --role lockbox.payloadViewer --service-account-id "$RUNTIME_SA_ID" >/dev/null
yc serverless container add-access-binding "$CONTAINER_ID" --role serverless-containers.containerInvoker --service-account-id "$GATEWAY_SA_ID" >/dev/null

yc container registry add-access-binding "$REGISTRY_ID" --role container-registry.images.pusher --service-account-id "$DEPLOY_SA_ID" >/dev/null
yc serverless container add-access-binding "$CONTAINER_ID" --role serverless-containers.editor --service-account-id "$DEPLOY_SA_ID" >/dev/null
yc ydb database add-access-binding "$YDB_ID" --role ydb.viewer --service-account-id "$DEPLOY_SA_ID" >/dev/null
yc lockbox secret add-access-binding "$OWNER_SECRET_ID" --role lockbox.viewer --service-account-id "$DEPLOY_SA_ID" >/dev/null
yc iam service-account add-access-binding "$RUNTIME_SA_ID" --role iam.serviceAccounts.user --service-account-id "$DEPLOY_SA_ID" >/dev/null
yc iam service-account add-access-binding "$GATEWAY_SA_ID" --role iam.serviceAccounts.user --service-account-id "$DEPLOY_SA_ID" >/dev/null

if ! yc serverless api-gateway get "$GATEWAY" --format json >/tmp/eksamio-brain-gateway.json 2>/dev/null; then
  cat >/tmp/eksamio-brain-gateway.yaml <<EOF_GATEWAY
openapi: "3.0.0"
info:
  title: Eksamio Brain Owner Console
  version: "1.0.0"
paths:
  /:
    x-yc-apigateway-any-method:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: ${CONTAINER_ID}
        service_account_id: ${GATEWAY_SA_ID}
  /{proxy+}:
    x-yc-apigateway-any-method:
      x-yc-apigateway-integration:
        type: serverless_containers
        container_id: ${CONTAINER_ID}
        service_account_id: ${GATEWAY_SA_ID}
      parameters:
        - explode: false
          in: path
          name: proxy
          required: false
          schema:
            default: '-'
            type: string
          style: simple
EOF_GATEWAY
  yc serverless api-gateway create \
    --name "$GATEWAY" \
    --description "Private Eksamio Brain gateway" \
    --spec /tmp/eksamio-brain-gateway.yaml \
    --execution-timeout 600s \
    --labels project=eksamio,plane=brain \
    --format json >/tmp/eksamio-brain-gateway.json
fi
GATEWAY_ID=$(jq -er '.id' /tmp/eksamio-brain-gateway.json)
GATEWAY_DOMAIN=$(jq -er '.domain' /tmp/eksamio-brain-gateway.json)

yc serverless api-gateway add-access-binding "$GATEWAY_ID" --role api-gateway.editor --service-account-id "$DEPLOY_SA_ID" >/dev/null
ensure_federated_credential "$DEPLOY_SA_ID" "$FEDERATION_ID"
YDB_ENDPOINT=$(yc ydb database get "$YDB_ID" --format json | jq -er '.endpoint')

cat <<EOF_RESULT

EKSAMIO_BRAIN_YANDEX_BOOTSTRAP=PASS
YC_BRAIN_FOLDER_ID=$FOLDER_ID
YC_BRAIN_DEPLOY_SA_ID=$DEPLOY_SA_ID
YC_BRAIN_RUNTIME_SA_ID=$RUNTIME_SA_ID
YC_BRAIN_GATEWAY_SA_ID=$GATEWAY_SA_ID
YC_BRAIN_REGISTRY_ID=$REGISTRY_ID
YC_BRAIN_CONTAINER_ID=$CONTAINER_ID
YC_BRAIN_YDB_ID=$YDB_ID
YC_BRAIN_YDB_ENDPOINT=$YDB_ENDPOINT
YC_BRAIN_OWNER_SECRET_ID=$OWNER_SECRET_ID
YC_BRAIN_GATEWAY_ID=$GATEWAY_ID
YC_BRAIN_GATEWAY_DOMAIN=$GATEWAY_DOMAIN
YC_BRAIN_WIF_ID=$FEDERATION_ID
WIF_SUBJECT=$GITHUB_SUBJECT
EOF_RESULT

if [[ "$OWNER_KEY_CREATED" == "1" ]]; then
  echo
  echo 'OWNER ACCESS KEY — SAVE THIS ONCE; DO NOT PASTE IT INTO CHAT:'
  cat /tmp/eksamio-brain-owner-key.ONCE
  echo
  rm -f /tmp/eksamio-brain-owner-key.ONCE
fi

rm -f /tmp/eksamio-brain-*.json /tmp/eksamio-brain-gateway.yaml
