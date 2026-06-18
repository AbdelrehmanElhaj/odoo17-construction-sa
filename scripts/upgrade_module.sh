#!/usr/bin/env bash
# Upgrade the construction_management module in production.
# Usage: ./scripts/upgrade_module.sh [module_name]
# Default module: construction_management

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

MODULE="${1:-construction_management}"
DB="ConstructionDB"
CONTAINER="odoo17"
LOG="$ROOT_DIR/logs/odoo.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Upgrading module: $MODULE on DB: $DB"

sudo docker exec "$CONTAINER" \
    odoo -d "$DB" \
         --update="$MODULE" \
         --stop-after-init \
         --log-level info

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Upgrade complete."

if [ -f "$LOG" ]; then
    echo "Last 10 log lines:"
    tail -10 "$LOG"
fi
