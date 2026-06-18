#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  demo_setup.sh — Create Odoo database, install construction_management
#                  module, and load demo data (Saudi projects, BOQ,
#                  contracts, certificates, payment schedule).
#
#  Usage:  ./scripts/demo_setup.sh [database_name]
#  Default database name: ConstructionDemo
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE="$(bash "$ROOT_DIR/.compose")"

DB_NAME="${1:-ConstructionDemo}"
ODOO_CONTAINER="cms-odoo"
DB_CONTAINER="cms-db"
DB_USER="odoo17"
DB_PASS="odoo17"
MODULE="construction_management"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/demo_setup_$(date +%Y%m%d_%H%M%S).log"

# ── Colors ────────────────────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[ OK ]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[FAIL]${NC}  $*" >&2; }
step()    { echo -e "\n${BOLD}${BLUE}▶  $*${NC}"; }
ruler()   { printf "${BLUE}%60s${NC}\n" | tr ' ' '═'; }

run_sql() {
    sudo docker exec -e PGPASSWORD="$DB_PASS" "$DB_CONTAINER" \
        psql -U "$DB_USER" "$DB_NAME" -tAc "$1" 2>/dev/null || echo "0"
}

db_exists() {
    sudo docker exec -e PGPASSWORD="$DB_PASS" "$DB_CONTAINER" \
        psql -U "$DB_USER" -tAc \
        "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" \
        postgres 2>/dev/null | grep -q 1
}

compose_cmd() {
    cd "$ROOT_DIR" && $COMPOSE "$@"
}

# ── Banner ────────────────────────────────────────────────────────────

echo ""
ruler
echo -e "${BOLD}  Odoo 17 — Construction Management Demo Setup${NC}"
ruler
echo ""
info "Database  : $DB_NAME"
info "Module    : $MODULE"
info "Container : $ODOO_CONTAINER"
info "Log file  : $LOG_FILE"

# ── Phase 1: Preflight ────────────────────────────────────────────────

step "Phase 1/5 — Preflight checks"

for cname in "$ODOO_CONTAINER" "$DB_CONTAINER"; do
    status=$(sudo docker inspect --format '{{.State.Status}}' "$cname" 2>/dev/null \
             || echo "missing")
    if [ "$status" = "running" ]; then
        success "Container $cname is running"
    else
        error "Container $cname is $status"
        echo    "  Start containers with: cd $ROOT_DIR && ./start.sh"
        exit 1
    fi
done

DISK_FREE=$(df --output=avail -m / | tail -1)
if [ "$DISK_FREE" -lt 500 ]; then
    error "Less than 500 MB free on /  ($DISK_FREE MB). Aborting."
    exit 1
fi
success "Disk OK (${DISK_FREE} MB free)"

mkdir -p "$LOG_DIR"

# ── Phase 2: Drop existing DB ─────────────────────────────────────────

step "Phase 2/5 — Database"

if db_exists; then
    warn "Database '$DB_NAME' already exists."
    echo -ne "  Drop and recreate? [y/N]: "
    read -r confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        info "Terminating active connections to $DB_NAME..."
        sudo docker exec -e PGPASSWORD="$DB_PASS" "$DB_CONTAINER" \
            psql -U "$DB_USER" postgres -c \
            "SELECT pg_terminate_backend(pid)
             FROM pg_stat_activity
             WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" \
            >/dev/null 2>&1 || true

        info "Dropping database $DB_NAME..."
        sudo docker exec -e PGPASSWORD="$DB_PASS" "$DB_CONTAINER" \
            dropdb -U "$DB_USER" "$DB_NAME"
        success "Database dropped."
    else
        info "Aborted — database unchanged."
        exit 0
    fi
else
    info "No existing database found — will create fresh."
fi

# ── Phase 3: Install module + demo data ───────────────────────────────

step "Phase 3/5 — Install module + demo data"
info "Running: odoo -d $DB_NAME -i $MODULE --stop-after-init"
info "This takes 3–8 minutes on first install. Streaming key events..."
echo ""

sudo docker exec "$ODOO_CONTAINER" \
    odoo \
    --database "$DB_NAME" \
    --init     "$MODULE" \
    --load-language ar_001 \
    --stop-after-init \
    --log-level info \
    2>&1 | tee "$LOG_FILE" | \
    grep --line-buffered -E \
      "Loading module|loading.*construction|Modules loaded|Registry loaded|ERROR|WARNING.*construction_management" \
    || true

INSTALL_EXIT="${PIPESTATUS[0]}"
echo ""

if [ "$INSTALL_EXIT" -ne 0 ]; then
    error "Installation exited with code $INSTALL_EXIT. Check: $LOG_FILE"
    exit 1
fi

# Verify module state in DB
MODULE_STATE=$(sudo docker exec -e PGPASSWORD="$DB_PASS" "$DB_CONTAINER" \
    psql -U "$DB_USER" "$DB_NAME" -tAc \
    "SELECT state FROM ir_module_module WHERE name='${MODULE}' LIMIT 1;" \
    2>/dev/null | tr -d '[:space:]')

if [ "$MODULE_STATE" = "installed" ]; then
    success "Module '$MODULE' → installed"
else
    error "Module state is '${MODULE_STATE}' (expected 'installed'). Check: $LOG_FILE"
    exit 1
fi

# ── Phase 4: Company setup ────────────────────────────────────────────

step "Phase 4/5 — Company setup"
info "Configuring company name, country, currency, and VAT for ZATCA..."

COMPANY_SCRIPT="
import odoo
from odoo.api import Environment
import odoo.modules.registry
odoo.tools.config.parse_config(['--database=$DB_NAME','--no-http','--log-level=error'])
registry = odoo.modules.registry.Registry('$DB_NAME')
with registry.cursor() as cr:
    env = Environment(cr, odoo.SUPERUSER_ID, {})
    company = env['res.company'].browse(1)
    sar = env.ref('base.SAR', raise_if_not_found=False)
    sa  = env.ref('base.sa',  raise_if_not_found=False)
    vals = {'name': 'شركة PropTech للإنشاءات والتطوير', 'vat': '310000000000001'}
    if sar: vals['currency_id'] = sar.id
    if sa:  vals['country_id'] = sa.id
    company.write(vals)
    cr.commit()
    print('Company configured.')
"

sudo docker exec "$ODOO_CONTAINER" python3 -c "$COMPANY_SCRIPT" 2>&1 | grep -v "^$" || true

success "Company set: شركة PropTech للإنشاءات والتطوير | VAT 310000000000001 | SAR | SA"

# ── Phase 5: Verification ─────────────────────────────────────────────

step "Phase 5/5 — Verification"

COUNT_PROJECTS=$(run_sql "SELECT COUNT(*) FROM construction_project;")
COUNT_BOQS=$(run_sql "SELECT COUNT(*) FROM construction_boq;")
COUNT_BOQ_LINES=$(run_sql "SELECT COUNT(*) FROM construction_boq_line;")
COUNT_CONTRACTS=$(run_sql "SELECT COUNT(*) FROM construction_contract;")
COUNT_SUBCONTRACTS=$(run_sql "SELECT COUNT(*) FROM construction_subcontract;")
COUNT_PAYMENTS=$(run_sql "SELECT COUNT(*) FROM construction_payment_line;")
COUNT_CERTS=$(run_sql "SELECT COUNT(*) FROM construction_certificate;")
COUNT_CERT_LINES=$(run_sql "SELECT COUNT(*) FROM construction_certificate_line;")
COUNT_CONTRACTORS=$(run_sql "SELECT COUNT(*) FROM res_partner WHERE is_contractor = true;")
TOTAL_CONTRACT_VALUE=$(run_sql "SELECT COALESCE(SUM(contract_value),0)::bigint FROM construction_contract;")

echo ""
echo -e "${BOLD}  Demo data loaded:${NC}"
echo "  ┌──────────────────────────────────────────────┐"
printf "  │  %-30s %10s  │\n" "Projects"            "$COUNT_PROJECTS"
printf "  │  %-30s %10s  │\n" "BOQs"                "$COUNT_BOQS"
printf "  │  %-30s %10s  │\n" "BOQ Lines"           "$COUNT_BOQ_LINES"
printf "  │  %-30s %10s  │\n" "Contracts"           "$COUNT_CONTRACTS"
printf "  │  %-30s %10s  │\n" "Subcontracts"        "$COUNT_SUBCONTRACTS"
printf "  │  %-30s %10s  │\n" "Payment Milestones"  "$COUNT_PAYMENTS"
printf "  │  %-30s %10s  │\n" "Certificates"        "$COUNT_CERTS"
printf "  │  %-30s %10s  │\n" "Certificate Lines"   "$COUNT_CERT_LINES"
printf "  │  %-30s %10s  │\n" "Contractors"         "$COUNT_CONTRACTORS"
echo "  ├──────────────────────────────────────────────┤"
printf "  │  %-30s %10s  │\n" "Total Contract Value (SAR)" "$(printf '%d' "$TOTAL_CONTRACT_VALUE" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')"
echo "  └──────────────────────────────────────────────┘"

# ── Access info ───────────────────────────────────────────────────────

echo ""
ruler
echo -e "${BOLD}${GREEN}  Setup complete!${NC}"
ruler
echo ""
echo -e "  ${BOLD}Browser access:${NC}"
echo    "  The demo database is ready. To access it via browser:"
echo    ""
echo    "  Option 1 — Temporarily allow any DB (revert after demo):"
echo    "    sudo sed -i 's/dbfilter.*/dbfilter = .*/' \\"
echo    "      /home/ubuntu/odoo17-construction-sa/config/odoo.conf"
echo    "    cd $ROOT_DIR && $COMPOSE restart web"
echo    "    # Then visit https://csm.hdrelhaj.com and switch to $DB_NAME"
echo    "    # Login: admin / admin"
echo    ""
echo    "  Option 2 — Switch production to the demo DB:"
echo    "    sudo sed -i \"s/dbfilter.*/dbfilter = ^${DB_NAME}\$/\" \\"
echo    "      /home/ubuntu/odoo17-construction-sa/config/odoo.conf"
echo    "    cd $ROOT_DIR && $COMPOSE restart web"
echo    ""
echo    "  Option 3 — Restore production DB when done:"
echo    "    sudo sed -i 's/dbfilter.*/dbfilter = ^ConstructionDB\$/' \\"
echo    "      /home/ubuntu/odoo17-construction-sa/config/odoo.conf"
echo    "    cd $ROOT_DIR && $COMPOSE restart web"
echo    ""
echo    "  Full log: $LOG_FILE"
echo ""
