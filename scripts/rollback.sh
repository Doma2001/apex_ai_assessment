#!/usr/bin/env bash
set -euo pipefail
PREV="$(cat .previous_version 2>/dev/null || echo none)"
[ "$PREV" != "none" ] || { echo "no previous version recorded"; exit 1; }
APP_VERSION="$PREV" docker compose up -d --no-build
curl -fs --retry 10 --retry-delay 2 --retry-connrefused localhost:8000/health
echo "$PREV" > .current_version; echo; echo "rolled back to $PREV"
