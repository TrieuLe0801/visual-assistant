#!/usr/bin/env bash
set -Eeuo pipefail

deploy_dir="${DEPLOY_DIR:-$(pwd)}"
backup_dir="${BACKUP_DIR:-$deploy_dir/backups/ci-cd}"
release_id="${RELEASE_ID:-manual-$(date -u +%Y%m%dT%H%M%SZ)}"
compose=(docker compose --project-name visual-assistant --project-directory "$deploy_dir")

cd "$deploy_dir"
test -f .deploy-target
test "$(cat .deploy-target)" = image-studio-compose-host
test -f .env
test -f .secrets/session_secret
test -f compose.yaml
mkdir -p "$backup_dir"

test "$(docker compose ls --all --format json | python -c 'import json,sys; rows=json.load(sys.stdin); print(any(row.get("Name") == "visual-assistant" for row in rows))')" = True
volume_name="$(docker compose config --format json | python -c 'import json,sys; print(json.load(sys.stdin)["volumes"]["image_data"]["name"])')"
docker volume inspect "$volume_name" >/dev/null
archive="$backup_dir/image-studio-${release_id}.tgz"

previous_app="$(docker image inspect image-studio:local --format '{{.Id}}' 2>/dev/null || true)"
previous_frontend="$(docker image inspect image-studio-frontend:local --format '{{.Id}}' 2>/dev/null || true)"
if [[ -n "$previous_app" ]]; then docker image tag image-studio:local image-studio:rollback; fi
if [[ -n "$previous_frontend" ]]; then docker image tag image-studio-frontend:local image-studio-frontend:rollback; fi

rollback() {
  if [[ -n "$previous_app" ]]; then docker image tag image-studio:rollback image-studio:local; fi
  if [[ -n "$previous_frontend" ]]; then docker image tag image-studio-frontend:rollback image-studio-frontend:local; fi
  "${compose[@]}" up -d --no-build --wait app frontend || true
  "${compose[@]}" --profile publish up -d cloudflared || true
}
trap rollback ERR

"${compose[@]}" --profile publish stop cloudflared app frontend 2>/dev/null || true
docker run --rm --user 0 \
  --mount "type=volume,src=${volume_name},dst=/data,readonly" \
  --mount "type=bind,src=${backup_dir},dst=/backups" \
  image-studio:local tar -czf "/backups/$(basename "$archive")" -C /data .

"${compose[@]}" build app frontend
"${compose[@]}" up -d --wait app frontend
published_port="$("${compose[@]}" port frontend 80 | awk -F: '{print $NF}')"
curl --fail --silent --show-error --max-time 10 "http://127.0.0.1:${published_port}/api/health"
"${compose[@]}" --profile publish up -d cloudflared
trap - ERR
