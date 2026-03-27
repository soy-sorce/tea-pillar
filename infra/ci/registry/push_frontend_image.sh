#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="gcp-hackathon-2026"
REGION="asia-northeast1"
REPOSITORY="nekkoflix"
IMAGE_NAME="video-gen4cat-frontend"
TAG="${1:-initial}"

ROOT_DIR="/home/shouh/team_project/GCP_hackathon_2026/tea-pillar"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"

echo "==> configuring docker auth for Artifact Registry"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> building frontend image"
docker build \
  -f "${ROOT_DIR}/frontend/Dockerfile" \
  -t "${IMAGE_URI}" \
  "${ROOT_DIR}/frontend"

echo "==> pushing frontend image"
docker push "${IMAGE_URI}"

echo "done"
echo "image_uri=${IMAGE_URI}"
