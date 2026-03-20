#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="gcp-hackathon-2026"
REGION="asia-northeast1"
MODEL_IMAGE_NAME="nekkoflix-model"
MODEL_IMAGE_TAG="v0"
ARTIFACT_REGISTRY_REPO=""

usage() {
  cat <<'EOF'
Usage:
  bash scripts/deploy_ML/build_and_push_model.sh --artifact-registry-repo <repo>

Options:
  --artifact-registry-repo, --repo   Artifact Registry repository name
EOF
}

while (($# > 0)); do
  case "$1" in
    --artifact-registry-repo|--repo)
      ARTIFACT_REGISTRY_REPO="${2:-}"
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

ROOT_DIR="/home/shouh/team_project/GCP_hackathon_2026/tea-pillar"
MODEL_DIR="${ROOT_DIR}/model"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REGISTRY_REPO}/${MODEL_IMAGE_NAME}:${MODEL_IMAGE_TAG}"

echo "==> configuring docker auth for Artifact Registry"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> building model image locally"
docker build -t "${IMAGE_URI}" "${MODEL_DIR}"

echo "==> pushing model image"
docker push "${IMAGE_URI}"

echo "done"
echo "image_uri=${IMAGE_URI}"
