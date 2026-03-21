#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/shouh/team_project/GCP_hackathon_2026/tea-pillar"

BUILD_ARGS=()
DEPLOY_ARGS=()

usage() {
  cat <<'EOF'
Usage:
  bash scripts/deploy_ML/deploy_model_to_vertex.sh --artifact-registry-repo <repo> [--model-image-tag <tag>] [--vertex-model-display-name <name>]

Options:
  --artifact-registry-repo, --repo   Artifact Registry repository name
  --model-image-tag, --tag           Docker image tag
  --vertex-model-display-name, --display-name
                                    Vertex Model display name
EOF
}

while (($# > 0)); do
  case "$1" in
    --artifact-registry-repo|--repo)
      BUILD_ARGS+=("$1" "${2:-}")
      DEPLOY_ARGS+=("$1" "${2:-}")
      shift 2
      ;;
    --model-image-tag|--tag)
      BUILD_ARGS+=("$1" "${2:-}")
      DEPLOY_ARGS+=("$1" "${2:-}")
      shift 2
      ;;
    --vertex-model-display-name|--display-name)
      DEPLOY_ARGS+=("$1" "${2:-}")
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

"${ROOT_DIR}/scripts/deploy_ML/build_and_push_model.sh" "${BUILD_ARGS[@]}"
"${ROOT_DIR}/scripts/deploy_ML/deploy_vertex_model.sh" "${DEPLOY_ARGS[@]}"
