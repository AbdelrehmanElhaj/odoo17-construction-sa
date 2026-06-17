#!/usr/bin/env bash
# Upgrade the construction_management module in production.
# Usage: ./scripts/upgrade_module.sh [module_name]
# Default module: construction_management

set -euo pipefail

MODULE="${1:-construction_management}"
DB="ConstructionDB"
CONTAINER="odoo17"
LOG="/home/ubuntu/odoo17-construction-sa/logs/odoo.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Upgrading module: $MODULE on DB: $DB"

docker exec "$CONTAINER" \
    odoo -d "$DB" \
         --update="$MODULE" \
         --stop-after-init \
         1>/proc/1/fd/1 2>/proc/1/fd/2

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Upgrade complete. Last 10 log lines:"
tail -10 "$LOG"
