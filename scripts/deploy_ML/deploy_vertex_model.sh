#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="gcp-hackathon-2026"
REGION="asia-northeast1"
MODEL_IMAGE_NAME="nekkoflix-model"
MODEL_IMAGE_TAG="v0"
VERTEX_MODEL_DISPLAY_NAME="nekkoflix-model-v0"
VERTEX_ENDPOINT_DISPLAY_NAME="nekkoflix-model-endpoint"
ARTIFACT_REGISTRY_REPO=""
UNDEPLOY_OLD_DEPLOYED_MODEL_ID=""

MACHINE_TYPE="${MACHINE_TYPE:-n1-standard-4}"
MIN_REPLICA_COUNT="${MIN_REPLICA_COUNT:-1}"
MAX_REPLICA_COUNT="${MAX_REPLICA_COUNT:-1}"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/deploy_ML/deploy_vertex_model.sh --artifact-registry-repo <repo> [--model-image-tag <tag>] [--vertex-model-display-name <name>] [--undeploy-old-deployed-model-id <id>]

Options:
  --artifact-registry-repo, --repo   Artifact Registry repository name
  --model-image-tag, --tag           Docker image tag (default: v0)
  --vertex-model-display-name, --display-name
                                    Vertex Model display name (default: nekkoflix-model-v0)
  --vertex-endpoint-display-name     Vertex Endpoint display name (default: nekkoflix-model-endpoint)
  --undeploy-old-deployed-model-id   Undeploy an old deployed model id after the new deployment succeeds
EOF
}

while (($# > 0)); do
  case "$1" in
    --artifact-registry-repo|--repo)
      ARTIFACT_REGISTRY_REPO="${2:-}"
      shift 2
      ;;
    --model-image-tag|--tag)
      MODEL_IMAGE_TAG="${2:-}"
      shift 2
      ;;
    --vertex-model-display-name|--display-name)
      VERTEX_MODEL_DISPLAY_NAME="${2:-}"
      shift 2
      ;;
    --vertex-endpoint-display-name)
      VERTEX_ENDPOINT_DISPLAY_NAME="${2:-}"
      shift 2
      ;;
    --undeploy-old-deployed-model-id)
      UNDEPLOY_OLD_DEPLOYED_MODEL_ID="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${ARTIFACT_REGISTRY_REPO}" ]]; then
  echo "missing required argument: --artifact-registry-repo" >&2
  usage >&2
  exit 1
fi

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${MODEL_IMAGE_NAME}:${MODEL_IMAGE_TAG}"

print_endpoint_state() {
  local endpoint_id="$1"
  echo "==> endpoint state"
  gcloud ai endpoints describe "${endpoint_id}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --format="yaml(displayName,name,trafficSplit,deployedModels.id,deployedModels.displayName,deployedModels.model,deployedModels.createTime)"
}

echo "==> uploading model to vertex ai"
upload_args=(
  ai models upload
  --project="${PROJECT_ID}"
  --region="${REGION}"
  --display-name="${VERTEX_MODEL_DISPLAY_NAME}"
  --container-image-uri="${IMAGE_URI}"
  --container-predict-route="/predict"
  --container-health-route="/health"
)

if [[ -n "${SERVICE_ACCOUNT_EMAIL:-}" ]]; then
  upload_args+=(--service-account="${SERVICE_ACCOUNT_EMAIL}")
fi

gcloud "${upload_args[@]}"

echo "==> creating endpoint if needed"
if ! gcloud ai endpoints list \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --filter="display_name=${VERTEX_ENDPOINT_DISPLAY_NAME}" \
  --format="value(name)" | grep -q .; then
  gcloud ai endpoints create \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --display-name="${VERTEX_ENDPOINT_DISPLAY_NAME}"
fi

MODEL_ID="$(gcloud ai models list \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --filter="display_name=${VERTEX_MODEL_DISPLAY_NAME}" \
  --sort-by="~createTime" \
  --limit=1 \
  --format="value(name)")"

ENDPOINT_ID="$(gcloud ai endpoints list \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --filter="display_name=${VERTEX_ENDPOINT_DISPLAY_NAME}" \
  --limit=1 \
  --format="value(name)")"

if [[ -z "${MODEL_ID}" || -z "${ENDPOINT_ID}" ]]; then
  echo "failed to resolve model id or endpoint id" >&2
  exit 1
fi

echo "==> deploying model to endpoint"
deploy_args=(
  ai endpoints deploy-model "${ENDPOINT_ID}"
  --project="${PROJECT_ID}"
  --region="${REGION}"
  --model="${MODEL_ID}"
  --display-name="${VERTEX_MODEL_DISPLAY_NAME}"
  --machine-type="${MACHINE_TYPE}"
  --min-replica-count="${MIN_REPLICA_COUNT}"
  --max-replica-count="${MAX_REPLICA_COUNT}"
)

if [[ -n "${SERVICE_ACCOUNT_EMAIL:-}" ]]; then
  deploy_args+=(--service-account="${SERVICE_ACCOUNT_EMAIL}")
fi

gcloud "${deploy_args[@]}"

if [[ -n "${UNDEPLOY_OLD_DEPLOYED_MODEL_ID}" ]]; then
  echo "==> undeploying old deployed model: ${UNDEPLOY_OLD_DEPLOYED_MODEL_ID}"
  gcloud ai endpoints undeploy-model "${ENDPOINT_ID}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --deployed-model-id="${UNDEPLOY_OLD_DEPLOYED_MODEL_ID}"
fi

echo "done"
echo "image_uri=${IMAGE_URI}"
echo "endpoint_id=${ENDPOINT_ID}"
print_endpoint_state "${ENDPOINT_ID}"
