#!/usr/bin/env bash
set -euo pipefail

if [[ "${KANBOARD_AUTOSTART:-1}" == "0" ]]; then
  echo "Kanboard Neo autostart is disabled for this session."
  exit 0
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HEALTH_URL="${KANBOARD_HEALTH_URL:-http://127.0.0.1/healthcheck.php}"
COMPOSE_FILE="${KANBOARD_COMPOSE_FILE:-$REPO_DIR/docker-compose.sqlite.yml}"

is_healthy() {
  curl --fail --silent --show-error --max-time 3 "$HEALTH_URL" >/dev/null 2>&1
}

if is_healthy; then
  echo "Kanboard Neo is already healthy."
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is unavailable; Kanboard Neo was not started." >&2
  exit 1
fi

echo "Kanboard Neo is stopped; starting the existing Compose stack."
docker compose -f "$COMPOSE_FILE" up -d

for _ in $(seq 1 20); do
  if is_healthy; then
    echo "Kanboard Neo is healthy."
    exit 0
  fi
  sleep 1
done

echo "Kanboard Neo did not become healthy within 20 seconds." >&2
exit 1
