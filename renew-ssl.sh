#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
COMPOSE="$(bash "$ROOT/.compose")"

echo "[$(date)] Running certbot renew..."
$COMPOSE run --rm --entrypoint certbot certbot renew --quiet

echo "[$(date)] Installing renewed certs..."
sudo cp "$ROOT/config/certbot/certs/live/sms.hdrelhaj.com/fullchain.pem" "$ROOT/config/certs/nginx.crt"
sudo cp "$ROOT/config/certbot/certs/live/sms.hdrelhaj.com/privkey.pem"   "$ROOT/config/certs/nginx.key"
sudo chown "$(id -u):$(id -g)" "$ROOT/config/certs/nginx.crt" "$ROOT/config/certs/nginx.key"

docker exec odoo17-nginx nginx -s reload
echo "[$(date)] Done."
