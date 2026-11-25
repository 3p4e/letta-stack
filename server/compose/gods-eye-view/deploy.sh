#!/usr/bin/env bash
# Run on KVM4 (via kvm4-runner /shell, or SSH): bash deploy.sh
# Idempotent. Installs nothing on the host beyond git/apache2-utils if missing; Node 24 lives in the image.
set -euo pipefail
STACK=/opt/stacks/gods-eye-view
REPO=https://github.com/bilawalsidhu/gods-eye-view.git
HOST_NAME="${GEV_HOST:-gev.srv1231216.hstgr.cloud}"

command -v git >/dev/null || { apt-get update -qq && apt-get install -y -qq git; }
command -v htpasswd >/dev/null || { apt-get update -qq && apt-get install -y -qq apache2-utils; }
docker network inspect traefik_network >/dev/null   # fail early if Traefik's network is not there

mkdir -p "$STACK"; cd "$STACK"
[ -d src/.git ] && git -C src pull --ff-only || git clone --depth 1 "$REPO" src
touch src/.env && chmod 600 src/.env
chown -R 1000:1000 src

if [ ! -f .env ]; then
  PASS=$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-20)
  HASH=$(htpasswd -nbB gev "$PASS" | sed -e 's/\$/\$\$/g')    # $$ = literal $ in compose
  printf 'GEV_HOST=%s\nGEV_BASICAUTH=%s\n' "$HOST_NAME" "$HASH" > .env; chmod 600 .env
  echo "basic-auth user=gev password=$PASS   (shown once; store it)"
fi
cp -f "$(dirname "$0")/docker-compose.yml" docker-compose.yml 2>/dev/null || true
docker compose up -d --build
sleep 20
docker compose ps
docker inspect gods-eye-view --format '{{.State.Health.Status}}'
curl -sk -o /dev/null -w "public (no auth) -> %{http_code} (expect 401)\n" "https://$HOST_NAME/"
