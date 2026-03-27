#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="gcp-hackathon-2026"
REGION="asia-northeast1"
REPOSITORY="nekkoflix"
IMAGE_NAME="video-gen4cat-backend"
TAG="${1:-initial}"

ROOT_DIR="/home/shouh/team_project/GCP_hackathon_2026/tea-pillar"
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"

echo "==> configuring docker auth for Artifact Registry"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> building backend image"
docker build \
  -f "${ROOT_DIR}/backend/Dockerfile" \
  -t "${IMAGE_URI}" \
  "${ROOT_DIR}"

echo "==> pushing backend image"
docker push "${IMAGE_URI}"

echo "done"
echo "image_uri=${IMAGE_URI}"
