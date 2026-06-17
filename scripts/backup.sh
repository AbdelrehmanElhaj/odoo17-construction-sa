#!/usr/bin/env bash
# Odoo 17 Construction Management — daily backup
# Usage: ./scripts/backup.sh
# Keeps 7 daily backups. Run via cron at 02:00.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$ROOT_DIR/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$BACKUP_DIR/backup.log"

DB_CONTAINER="odoo17-db"
ODOO_CONTAINER="odoo17"
DB_NAME="ConstructionDB"
DB_USER="odoo17"
DB_PASS="odoo17"

KEEP_DAYS=7

# ── helpers ───────────────────────────────────────────────────────────

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

check_disk() {
    local avail
    avail=$(df --output=avail -m "$BACKUP_DIR" | tail -1)
    if [ "$avail" -lt 200 ]; then
        log "ERROR: Less than 200 MB free on backup directory ($avail MB). Aborting."
        exit 1
    fi
    log "Disk OK: ${avail} MB free before backup."
}

# ── main ──────────────────────────────────────────────────────────────

mkdir -p "$BACKUP_DIR"

log "========== Backup started: $TIMESTAMP =========="

check_disk

# 1 — PostgreSQL dump
DB_FILE="$BACKUP_DIR/db_${DB_NAME}_${TIMESTAMP}.sql.gz"
log "Dumping database $DB_NAME → $(basename "$DB_FILE")"
docker exec -e PGPASSWORD="$DB_PASS" "$DB_CONTAINER" \
    pg_dump -U "$DB_USER" "$DB_NAME" \
    | gzip > "$DB_FILE"
log "Database dump complete: $(du -sh "$DB_FILE" | cut -f1)"

# 2 — Odoo filestore (attachments, sessions, etc.)
FS_FILE="$BACKUP_DIR/filestore_${TIMESTAMP}.tar.gz"
log "Archiving filestore → $(basename "$FS_FILE")"
docker exec "$ODOO_CONTAINER" \
    tar -czf - /var/lib/odoo/filestore 2>/dev/null \
    > "$FS_FILE" || true
log "Filestore archive complete: $(du -sh "$FS_FILE" | cut -f1)"

# 3 — Module source (addons only, lightweight)
ADDON_FILE="$BACKUP_DIR/addons_${TIMESTAMP}.tar.gz"
log "Archiving addons → $(basename "$ADDON_FILE")"
tar -czf "$ADDON_FILE" -C "$ROOT_DIR" addons/
log "Addons archive complete: $(du -sh "$ADDON_FILE" | cut -f1)"

# 4 — Purge old backups
log "Purging backups older than $KEEP_DAYS days..."
find "$BACKUP_DIR" -maxdepth 1 -name "*.gz" -mtime +"$KEEP_DAYS" -delete
find "$BACKUP_DIR" -maxdepth 1 -name "*.sql.gz" -mtime +"$KEEP_DAYS" -delete

TOTAL=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Backup dir total: $TOTAL"
log "========== Backup complete =========="
