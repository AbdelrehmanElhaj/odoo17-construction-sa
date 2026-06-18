#!/usr/bin/env bash
# Odoo 17 Construction Management — health check
# Exits 0 if healthy, 1 if any check fails.
# Usage: ./scripts/health_check.sh [--json]

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

JSON_MODE=false
[[ "${1:-}" == "--json" ]] && JSON_MODE=true

ODOO_URL="http://localhost:8069"
DISK_WARN_PCT=80
DISK_CRIT_PCT=90
RAM_WARN_MB=150

PASS=0; FAIL=1
overall=0

# ── helpers ───────────────────────────────────────────────────────────

ok()   { echo "  [OK]   $*"; }
warn() { echo "  [WARN] $*"; overall=1; }
fail() { echo "  [FAIL] $*"; overall=1; }

# ── checks ────────────────────────────────────────────────────────────

echo "=== Odoo Health Check — $(date '+%Y-%m-%d %H:%M:%S') ==="

# 1 — Docker containers
echo ""
echo "Containers:"
for cname in odoo17 odoo17-db; do
    status=$(docker inspect --format '{{.State.Status}}' "$cname" 2>/dev/null || echo "missing")
    if [ "$status" = "running" ]; then
        ok "$cname → running"
    else
        fail "$cname → $status"
    fi
done

# 2 — Nginx
echo ""
echo "Nginx:"
if systemctl is-active --quiet nginx; then
    ok "nginx.service → active"
else
    fail "nginx.service → inactive"
fi

# 3 — Odoo HTTP
echo ""
echo "Odoo HTTP:"
http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$ODOO_URL/web/database/selector" 2>/dev/null || echo "000")
if [[ "$http_code" == "200" || "$http_code" == "303" || "$http_code" == "302" ]]; then
    ok "GET $ODOO_URL → HTTP $http_code"
else
    fail "GET $ODOO_URL → HTTP $http_code (expected 200/303)"
fi

# 4 — Disk
echo ""
echo "Disk:"
root_pct=$(df / --output=pcent | tail -1 | tr -d ' %')
root_avail_mb=$(df / --output=avail -m | tail -1 | tr -d ' ')
if [ "$root_pct" -ge "$DISK_CRIT_PCT" ]; then
    fail "Root disk ${root_pct}% used (${root_avail_mb} MB free) — CRITICAL"
elif [ "$root_pct" -ge "$DISK_WARN_PCT" ]; then
    warn "Root disk ${root_pct}% used (${root_avail_mb} MB free) — resize EBS recommended"
else
    ok "Root disk ${root_pct}% used (${root_avail_mb} MB free)"
fi

# 5 — RAM
echo ""
echo "RAM:"
avail_mb=$(awk '/MemAvailable/ { printf "%.0f", $2/1024 }' /proc/meminfo)
if [ "$avail_mb" -lt "$RAM_WARN_MB" ]; then
    warn "Available RAM: ${avail_mb} MB — consider adding swap or upgrading instance"
else
    ok "Available RAM: ${avail_mb} MB"
fi

# 6 — SSL certificate expiry
echo ""
echo "SSL:"
cert="/etc/letsencrypt/live/csm.hdrelhaj.com/fullchain.pem"
if sudo test -f "$cert"; then
    expiry=$(sudo openssl x509 -enddate -noout -in "$cert" 2>/dev/null | cut -d= -f2)
    days_left=$(( ( $(date -d "$expiry" +%s) - $(date +%s) ) / 86400 ))
    if [ "$days_left" -lt 14 ]; then
        fail "SSL cert expires in ${days_left} days ($expiry)"
    elif [ "$days_left" -lt 30 ]; then
        warn "SSL cert expires in ${days_left} days ($expiry)"
    else
        ok "SSL cert valid for ${days_left} more days"
    fi
else
    warn "SSL cert not found at $cert"
fi

# 7 — Odoo log errors in last hour
echo ""
echo "Odoo log (last hour):"
LOG="$ROOT_DIR/logs/odoo.log"
if [ -f "$LOG" ]; then
    errors=$(awk -v d="$(date -d '1 hour ago' '+%Y-%m-%d %H:%M')" '$0 >= d && /ERROR/' "$LOG" | wc -l)
    if [ "$errors" -gt 0 ]; then
        warn "${errors} ERROR line(s) in the last hour — check $LOG"
    else
        ok "No ERROR lines in the last hour"
    fi
else
    warn "Log file not found at $LOG"
fi

# ── summary ───────────────────────────────────────────────────────────

echo ""
if [ "$overall" -eq 0 ]; then
    echo "=== HEALTHY ==="
else
    echo "=== DEGRADED — review WARN/FAIL items above ==="
fi

exit "$overall"
