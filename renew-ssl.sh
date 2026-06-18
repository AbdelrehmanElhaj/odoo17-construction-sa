#!/bin/bash
# Renew Let's Encrypt certificate for csm.hdrelhaj.com using host certbot.
# Safe to run at any time; certbot skips renewal if cert has >30 days remaining.
# Cron: 0 3 * * 1  (Mondays 03:00)  - runs weekly, renews when < 30 days left.

set -euo pipefail

DOMAIN="csm.hdrelhaj.com"
LOG_DIR="$(cd "$(dirname "$0")" && pwd)/logs"
LOG_FILE="$LOG_DIR/ssl-renew.log"

mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "=== SSL renewal started ==="

# Check current expiry before renewing
CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
if sudo test -f "$CERT"; then
    EXPIRY=$(sudo openssl x509 -enddate -noout -in "$CERT" 2>/dev/null | cut -d= -f2)
    DAYS_LEFT=$(( ( $(date -d "$EXPIRY" +%s) - $(date +%s) ) / 86400 ))
    log "Current cert expires in ${DAYS_LEFT} days ($EXPIRY)"
else
    log "WARNING: cert not found at $CERT — will attempt fresh issuance"
fi

# Run certbot renew (skips if > 30 days remaining)
log "Running: certbot renew --quiet"
sudo certbot renew --quiet --no-random-sleep-on-renew 2>&1 | tee -a "$LOG_FILE"

# Reload nginx to pick up renewed cert
log "Reloading nginx..."
sudo systemctl reload nginx

log "=== SSL renewal complete ==="
