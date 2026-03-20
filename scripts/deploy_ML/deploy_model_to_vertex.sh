#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/shouh/team_project/GCP_hackathon_2026/tea-pillar"

"${ROOT_DIR}/scripts/deploy_ML/build_and_push_model.sh" "$@"
"${ROOT_DIR}/scripts/deploy_ML/deploy_vertex_model.sh" "$@"
