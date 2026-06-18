#!/bin/bash
# Obtain a Let's Encrypt certificate using host certbot (webroot method).
# Requires: certbot installed, nginx running, port 80 open.
#
# Usage:
#   ./setup-ssl.sh                          # use default domain csm.hdrelhaj.com
#   ./setup-ssl.sh yourdomain.com           # use custom domain
#   LETSENCRYPT_EMAIL=you@example.com ./setup-ssl.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

DOMAIN="${1:-csm.hdrelhaj.com}"
EMAIL="${LETSENCRYPT_EMAIL:-a.elhaj@proptech.sa}"
WEBROOT="/var/www/certbot"

echo "=========================================="
echo "  SSL Setup — Let's Encrypt (host certbot)"
echo "  Domain: $DOMAIN"
echo "  Email:  $EMAIL"
echo "=========================================="
echo ""

# Verify certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "ERROR: certbot not installed."
    echo "  Install with: sudo apt-get install -y certbot python3-certbot-nginx"
    exit 1
fi

# Verify nginx is running
if ! systemctl is-active --quiet nginx; then
    echo "ERROR: nginx is not running. Start it first: sudo systemctl start nginx"
    exit 1
fi

# Create webroot for ACME challenge
sudo mkdir -p "$WEBROOT/.well-known/acme-challenge"

# Test HTTP challenge reachability
CHALLENGE_FILE="$WEBROOT/.well-known/acme-challenge/test-$(date +%s)"
echo "ok" | sudo tee "$CHALLENGE_FILE" > /dev/null
HTTP_CODE="$(curl -sf --max-time 10 "http://$DOMAIN/.well-known/acme-challenge/$(basename "$CHALLENGE_FILE")" \
    -o /dev/null -w '%{http_code}' 2>/dev/null || echo '000')"
sudo rm -f "$CHALLENGE_FILE"

if [ "$HTTP_CODE" != "200" ]; then
    echo "ERROR: ACME challenge path not reachable (HTTP $HTTP_CODE)."
    echo "  Ensure port 80 is open and nginx serves /.well-known/acme-challenge/ from $WEBROOT"
    exit 1
fi
echo "HTTP challenge verified (HTTP $HTTP_CODE)"
echo ""

# Check if cert already exists
CERT="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
if sudo test -f "$CERT"; then
    EXPIRY=$(sudo openssl x509 -enddate -noout -in "$CERT" 2>/dev/null | cut -d= -f2)
    DAYS_LEFT=$(( ( $(date -d "$EXPIRY" +%s) - $(date +%s) ) / 86400 ))
    echo "Certificate already exists — expires in ${DAYS_LEFT} days ($EXPIRY)."
    echo "To force renewal: sudo certbot renew --force-renewal --cert-name $DOMAIN"
    echo "To run renewal:   ./renew-ssl.sh"
    exit 0
fi

echo "Requesting certificate from Let's Encrypt..."
sudo certbot certonly \
    --webroot \
    --webroot-path "$WEBROOT" \
    --domain "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive

# Update nginx site config to reference the new cert
NGINX_CONF="/etc/nginx/sites-available/odoo"
if sudo grep -q "ssl_certificate" "$NGINX_CONF"; then
    sudo sed -i "s|ssl_certificate .*|ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|" "$NGINX_CONF"
    sudo sed -i "s|ssl_certificate_key .*|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|" "$NGINX_CONF"
    echo "Updated $NGINX_CONF with new cert paths."
fi

sudo nginx -t && sudo systemctl reload nginx

# Add weekly renewal cron
CRON_CMD="0 3 * * 1 cd $ROOT && bash renew-ssl.sh >> $ROOT/logs/ssl-renew.log 2>&1"
( sudo crontab -l 2>/dev/null | grep -v "renew-ssl.sh"; echo "$CRON_CMD" ) | sudo crontab -
echo "Weekly renewal cron added (Mondays 03:00)."

echo ""
echo "=========================================="
echo "  HTTPS is live: https://$DOMAIN"
echo "  Renewal script: ./renew-ssl.sh"
echo "=========================================="
