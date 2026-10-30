#!/usr/bin/env bash
set -euo pipefail
V="${1:?usage: scripts/deploy.sh <version>}"
cat .current_version 2>/dev/null > .previous_version || echo none > .previous_version
APP_VERSION="$V" docker compose up -d --build
for _ in $(seq 1 20); do
  if curl -fs localhost:8000/ready >/dev/null; then
    echo "$V" > .current_version; echo "deployed $V"; exit 0
  fi
  sleep 2
done
echo "readiness failed -> auto rollback"; ./scripts/rollback.sh; exit 1
