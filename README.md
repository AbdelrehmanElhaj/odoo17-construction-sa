# Odoo 17 — Construction Management System
### نظام إدارة مشاريع المقاولات | Saudi Market Edition

A production-ready Odoo 17 deployment for Saudi construction project management,
running on Docker with Let's Encrypt SSL, nginx reverse proxy, and a custom
`construction_management` module built for the Saudi market.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Module Features](#module-features)
3. [Directory Structure](#directory-structure)
4. [Quick Start](#quick-start)
5. [Day-to-Day Operations](#day-to-day-operations)
6. [Scripts Reference](#scripts-reference)
7. [Configuration](#configuration)
8. [Module Development](#module-development)
9. [Backup & Restore](#backup--restore)
10. [Troubleshooting](#troubleshooting)

---

## Architecture

```
Internet
   │
   ▼
[Host nginx]  ← systemd service, Let's Encrypt SSL (cms.hdrelhaj.com)
   │  proxy_pass 127.0.0.1:8069
   ▼
[cms-odoo container]  ← custom image built from Dockerfile
   │  db connection (internal Docker network)
   ▼
[cms-db container]  ← postgres:15
```

| Component | Details |
|---|---|
| Domain | `cms.hdrelhaj.com` |
| SSL | Let's Encrypt via host `certbot` + host nginx |
| Odoo version | 17.0 |
| Database | PostgreSQL 15, db name `ConstructionDB` |
| Odoo image | `odoo17-construction:latest` (built from `Dockerfile`) |
| Host OS | Ubuntu, AWS EC2 (eu-north-1) |
| Odoo port | `127.0.0.1:8069` (localhost only — nginx proxies it) |

**Why host nginx instead of Docker nginx?**
The host nginx holds the Let's Encrypt certificates and was already running.
Using a Docker nginx container for SSL would require sharing the cert volume
or duplicating renewal logic. The host nginx is simpler and already working.

---

## Module Features

The `construction_management` addon (`addons/construction_management/`) provides
a complete Arabic-first construction ERP for the Saudi market.

### Models

| Model | Arabic Name | Description |
|---|---|---|
| `construction.project` | مشروع المقاولات | Projects with Saudi national address, permits, progress % |
| `construction.boq` | جدول الكميات | Bill of Quantities with Excel/CSV import wizard |
| `construction.boq.line` | بند BOQ | BOQ line items (material, labor, equipment, subcontract, overhead) |
| `construction.contract` | عقد المقاولات | Main contracts with payment schedule |
| `construction.subcontract` | عقد الباطن | Subcontracts linked to main contracts |
| `construction.payment.line` | دفعة مجدولة | Payment milestones (advance, milestone, retention, final) |
| `construction.certificate` | مستخلص التقدم | Progress certificates — 4-stage approval workflow |
| `construction.certificate.line` | بند المستخلص | Certificate line items linked back to BOQ lines |
| `construction.dashboard` | لوحة المتابعة | KPI dashboard (projects, financials, certificates, payments) |
| `construction.saudi.region` | المنطقة الإدارية | Saudi administrative regions |
| `construction.saudi.city` | المدينة | Saudi cities (linked to regions) |
| `res.partner` (extension) | شريك الأعمال | Saudi ID, national address, contractor fields, phone validation |

### Key Features

- **Saudi National Address** on projects and partners (building no., street, secondary no., district, city, region, postal code — validated to Saudi Post standard)
- **ZATCA Phase 1 QR code** on progress certificates (TLV-encoded, base64)
- **BOQ Excel/CSV import wizard** — download template, upload filled file; supports `openpyxl` for `.xlsx`
- **4-stage certificate approval**: Draft → Under Review → Approved → Paid
- **Retention & advance deduction** auto-calculated on certificates
- **VAT 15%** on certificates with amount-with-VAT field
- **Arabic RTL PDF reports** for BOQ, contracts, and certificates
- **Dashboard KPIs**: active projects, total contract value, certified amount, overdue payments
- **Saudi ID validation**: national ID (starts with 1), Iqama (starts with 2), CR (10 digits)
- **Saudi phone validation**: mobile (`05XXXXXXXX`), work (`01XXXXXXXX`), WhatsApp (`+9665XXXXXXXX`)
- **Certificate amount validation** — prevents certifying beyond the contract value; also blocks overlapping certificate periods on the same contract
- **Retention release workflow** — tracks total retention held vs released; "إفراج الضمان" button on active contracts creates a payment line for the outstanding balance
- **Contract amendments** — amendment and addendum types link to a parent main contract via `parent_contract_id`; delta tracked via `amendment_value`; `effective_contract_value` computed on the main contract
- **Workflow notifications** — certificate state transitions schedule Odoo To-Do activities for the reviewer (on submit) and accountant (on approve); approval posts a financial summary note in chatter
- **Expiry monitoring** — `license_status` on contractor partners (30-day window); `permit_status` on projects (60-day window); daily cron auto-schedules activities for expiring/expired records; dashboard row shows 4 expiry KPI cards
- **Dashboard performance** — KPIs now use `search_count` and `read_group` DB aggregates instead of loading all records into Python memory; "Refresh" button added

### Security Groups

| Group | Arabic | Permissions |
|---|---|---|
| Viewer | مستخدم عرض | Read-only on all models |
| Engineer | مهندس موقع | Read + write + create (no delete) |
| Accountant | محاسب المقاولات | Read + write on contracts and payments |
| Manager | مدير المشاريع | Full access (includes Engineer + Accountant + Viewer) |

### Sequences

| Code | Format | Example |
|---|---|---|
| `construction.project` | `PROJ-YYYY-NNNN` | `PROJ-2026-0001` |
| `construction.boq` | `BOQ-YYYY-NNNN` | `BOQ-2026-0001` |
| `construction.contract` | `CONT-YYYY-NNNN` | `CONT-2026-0001` |
| `construction.subcontract` | `SUB-YYYY-NNNN` | `SUB-2026-0001` |
| `construction.certificate` | `CERT-YYYY-NNNN` | `CERT-2026-0001` |

---

## Directory Structure

```
odoo17-construction-sa/
├── Dockerfile                   # Extends odoo:17.0 — adds openpyxl + qrcode[pil]
├── docker-compose.yml           # db + web services
├── start.sh                     # Start all containers (builds image if needed)
├── stop.sh                      # Stop all containers
├── logs.sh                      # Tail Odoo logs
├── setup-ssl.sh                 # Initial Let's Encrypt certificate setup
├── renew-ssl.sh                 # Manual SSL renewal
├── install-docker.sh            # One-time Docker install script
├── universal_odoo17_setup.sh    # Full server setup automation
│
├── config/
│   ├── odoo.conf                # Odoo server configuration
│   ├── nginx.conf               # nginx site config (used if running Docker nginx)
│   └── certs/                   # Self-signed cert (fallback; real certs are in /etc/letsencrypt)
│
├── addons/
│   └── construction_management/ # Custom Odoo module
│       ├── __manifest__.py
│       ├── models/
│       │   ├── saudi_address.py          # Region + City models
│       │   ├── res_partner.py            # Partner extension (Saudi fields)
│       │   ├── construction_project.py   # Project model
│       │   ├── construction_boq.py       # BOQ + BOQ Line models
│       │   ├── construction_contract.py  # Contract + Subcontract + Payment Line
│       │   ├── construction_certificate.py # Certificate + Certificate Line + ZATCA QR
│       │   └── construction_dashboard.py # Dashboard KPIs
│       ├── views/                        # Form, list, kanban, search views
│       ├── reports/                      # QWeb PDF reports (BOQ, contract, certificate)
│       ├── wizards/
│       │   └── boq_import_wizard.py      # Excel/CSV BOQ import
│       ├── security/
│       │   ├── construction_security.xml # Groups definition
│       │   └── ir.model.access.csv       # ACL rules
│       ├── data/
│       │   ├── construction_sequences.xml
│       │   ├── expiry_cron.xml           # Daily cron for license/permit expiry monitoring
│       │   └── saudi_cities.xml          # All Saudi regions + cities
│       ├── demo/
│       │   └── demo_data.xml             # Sample projects, BOQ, contracts, certificates
│       └── i18n/
│           └── ar.po                     # Arabic translations
│
├── scripts/
│   ├── backup.sh           # PostgreSQL dump + filestore + addons archive (7-day retention)
│   ├── health_check.sh     # Check containers, nginx, HTTP, disk, RAM, SSL, log errors
│   ├── upgrade_module.sh   # Upgrade construction_management on ConstructionDB
│   └── demo_setup.sh       # Create a demo database with module + demo data loaded
│
├── backups/                # Backup output directory (auto-created by backup.sh)
└── logs/
    └── odoo.log            # Odoo server log (mounted from container)
```

---

## Quick Start

### Prerequisites

- Ubuntu 20.04+ server
- Docker + docker-compose installed (`./install-docker.sh` if needed)
- Domain pointed at your server IP (`cms.hdrelhaj.com`)

### First-time setup

```bash
# 1. Clone the repo
git clone <repo-url> /home/ubuntu/odoo17-construction-sa
cd /home/ubuntu/odoo17-construction-sa

# 2. Install SSL (Let's Encrypt) — requires domain to be live
sudo ./setup-ssl.sh

# 3. Start containers (builds custom Docker image on first run)
./start.sh

# 4. Open https://cms.hdrelhaj.com
#    Create database: ConstructionDB
#    Admin password: see config/odoo.conf (admin_passwd)

# 5. Install the construction_management module via Odoo Apps menu
#    or via CLI:
sudo docker exec cms-odoo odoo -d ConstructionDB \
    --init construction_management --stop-after-init
```

### Start / Stop

```bash
./start.sh    # Start containers (builds image if missing)
./stop.sh     # Stop containers (data preserved in Docker volumes)
./logs.sh     # Follow live Odoo log
```

---

## Day-to-Day Operations

### Check everything is healthy

```bash
./scripts/health_check.sh
# or with JSON output:
./scripts/health_check.sh --json
```

Checks: Docker container status, host nginx, Odoo HTTP, disk %, available RAM,
SSL certificate expiry, ERROR lines in the last hour.

### Follow logs

```bash
./logs.sh
# or directly:
tail -f logs/odoo.log
# Filter errors only:
grep ERROR logs/odoo.log | tail -20
```

### Restart Odoo only (without touching the database)

```bash
sudo docker-compose restart web
```

### Rebuild image (after Dockerfile changes)

```bash
sudo docker-compose build web
sudo docker-compose up -d web
```

---

## Scripts Reference

### `./scripts/backup.sh`

Creates three archives in `backups/`:
1. `db_ConstructionDB_TIMESTAMP.sql.gz` — PostgreSQL dump
2. `filestore_TIMESTAMP.tar.gz` — Odoo filestore (attachments)
3. `addons_TIMESTAMP.tar.gz` — Module source code

Automatically deletes archives older than 7 days. Aborts if less than 200 MB free.

**Cron (daily at 02:00):**
```bash
0 2 * * * /home/ubuntu/odoo17-construction-sa/scripts/backup.sh
```

### `./scripts/health_check.sh [--json]`

Exit code 0 = healthy, 1 = degraded. Suitable for cron alerting:

```bash
# Alert by email if degraded
0 * * * * /home/ubuntu/odoo17-construction-sa/scripts/health_check.sh || \
    mail -s "Odoo Health DEGRADED" admin@example.com
```

### `./scripts/upgrade_module.sh [module_name]`

Upgrades `construction_management` (or any module you pass) on `ConstructionDB`.
Safe to run while the server is running — Odoo handles the upgrade atomically.

```bash
./scripts/upgrade_module.sh
# or for a different module:
./scripts/upgrade_module.sh base
```

### `./scripts/demo_setup.sh [database_name]`

Creates a fresh database (`ConstructionDemo` by default), installs the module
with demo data, and configures the company for PropTech SA. Useful for testing
or demos without touching production data.

```bash
./scripts/demo_setup.sh
# custom name:
./scripts/demo_setup.sh ClientDemo
```

---

## Configuration

### `config/odoo.conf`

| Setting | Value | Notes |
|---|---|---|
| `admin_passwd` | `admin@123` | Master password for DB manager |
| `list_db` | `False` | Hides database selector from public |
| `dbfilter` | `^ConstructionDB$` | Only serves this database |
| `addons_path` | `/usr/lib/python3/.../odoo/addons,/mnt/extra-addons` | Custom addons from `./addons/` |
| `workers` | `0` | Single-process mode (safe for 2 GB RAM) |
| `max_cron_threads` | `1` | One cron thread |
| `limit_time_cpu` | `600` | For slow PDF/Excel operations |
| `limit_time_real` | `1200` | For slow PDF/Excel operations |
| `proxy_mode` | `True` | Trust X-Forwarded-* headers from nginx |
| `log_level` | `info` | Overall log level |
| `log_handler` | `:WARNING,odoo.addons.construction_management:INFO` | Silence noisy core; keep module at INFO |

### `Dockerfile`

```dockerfile
FROM odoo:17.0
USER root
RUN pip3 install --no-cache-dir openpyxl==3.1.5 qrcode[pil]==7.4.2
USER odoo
```

Extra packages installed:
- **`openpyxl`** — required for the BOQ Excel import wizard
- **`qrcode[pil]`** — required for ZATCA QR code generation on certificates

### `docker-compose.yml`

Two services: `db` (postgres:15) and `web` (custom Odoo image).
Port `127.0.0.1:8069:8069` is published so host nginx can reach Odoo.
All data is stored in named Docker volumes (`odoo-web-data`, `odoo-db-data`)
and survives container restarts and image rebuilds.

---

## Module Development

### Apply code changes without restarting

If you only changed Python model code or XML views:

```bash
./scripts/upgrade_module.sh
```

This runs `odoo --update construction_management --stop-after-init` inside
the container, then the running server picks up the changes on next request.

### Full restart after major changes

```bash
sudo docker-compose restart web
```

### Run with debug logging

```bash
sudo docker exec -it cms-odoo odoo \
    --config=/etc/odoo/odoo.conf \
    --database=ConstructionDB \
    --log-level=debug \
    --log-handler=odoo.addons.construction_management:DEBUG
```

### Python shell access

```bash
sudo docker exec -it cms-odoo odoo shell \
    --config=/etc/odoo/odoo.conf \
    --database=ConstructionDB
```

```python
# Example: count projects
env['construction.project'].search_count([])
# Example: check a certificate
cert = env['construction.certificate'].browse(1)
print(cert.amount_with_vat, cert.zatca_qr_code[:20])
```

### i18n / Translations

The `i18n/ar.po` file provides Arabic translations. Every entry requires a
`#. module: construction_management` comment (Odoo's parser enforces this).
Since all field labels are already bilingual inline (e.g. `'اسم المشروع | Project Name'`),
the PO file supplements rather than replaces them.

To regenerate translations from current model/view definitions:
```bash
sudo docker exec cms-odoo odoo \
    -d ConstructionDB \
    --i18n-export /tmp/construction_management_ar.po \
    --language ar_SA \
    --modules construction_management \
    --stop-after-init
sudo docker cp cms-odoo:/tmp/construction_management_ar.po \
    addons/construction_management/i18n/ar.po
```

---

## Backup & Restore

### Manual backup

```bash
./scripts/backup.sh
ls -lh backups/
```

### Restore from backup

```bash
# 1. Stop Odoo
./stop.sh

# 2. Drop and recreate the database
sudo docker start cms-db
sudo docker exec -e PGPASSWORD=odoo17 cms-db \
    dropdb -U odoo17 ConstructionDB
sudo docker exec -e PGPASSWORD=odoo17 cms-db \
    createdb -U odoo17 ConstructionDB

# 3. Restore PostgreSQL dump
gunzip -c backups/db_ConstructionDB_TIMESTAMP.sql.gz | \
sudo docker exec -i -e PGPASSWORD=odoo17 cms-db \
    psql -U odoo17 ConstructionDB

# 4. Restore filestore
sudo docker start cms-odoo
sudo docker exec -i cms-odoo \
    tar -xzf - -C / < backups/filestore_TIMESTAMP.tar.gz

# 5. Start everything
./start.sh
```

### Automated daily backup (cron)

```bash
crontab -e
# Add:
0 2 * * * /home/ubuntu/odoo17-construction-sa/scripts/backup.sh >> /home/ubuntu/odoo17-construction-sa/logs/cron.log 2>&1
```

---

## Troubleshooting

### Odoo won't start

```bash
# Check container logs
sudo docker logs cms-odoo 2>&1 | tail -30
# Check Odoo application log
tail -50 logs/odoo.log
# Verify database is reachable
sudo docker exec cms-db pg_isready -U odoo17
```

### HTTP 502 Bad Gateway from nginx

The host nginx proxies to `127.0.0.1:8069`. Check:

```bash
# Is Odoo listening on 8069?
sudo ss -tlnp | grep 8069
# Is the container running?
sudo docker ps | grep cms-odoo
# Direct test (bypasses nginx)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8069/web/login
```

If the port is not bound, the container may have restarted without the port mapping:
```bash
sudo docker-compose up -d web
```

### Module not visible in Odoo Apps

```bash
# Refresh module list from inside Odoo: Settings → Apps → Update Apps List
# Or via CLI:
sudo docker exec cms-odoo odoo \
    -d ConstructionDB \
    --update base \
    --stop-after-init
```

### openpyxl / qrcode missing after container restart

The `Dockerfile` bakes these packages into the image. If the old `odoo:17.0`
image was used instead of the custom build:

```bash
sudo docker-compose build web
sudo docker-compose up -d web
```

### Database filter blocking access

`odoo.conf` is set to `dbfilter = ^ConstructionDB$`. To temporarily access
other databases (e.g. the demo DB):

```bash
sudo sed -i 's/^dbfilter.*/dbfilter = .*/' config/odoo.conf
sudo docker-compose restart web
# ... use demo DB ...
# Restore:
sudo sed -i 's/^dbfilter.*/dbfilter = ^ConstructionDB$/' config/odoo.conf
sudo docker-compose restart web
```

### SSL certificate expired or missing

```bash
# Check expiry
sudo openssl x509 -enddate -noout \
    -in /etc/letsencrypt/live/cms.hdrelhaj.com/fullchain.pem
# Renew manually
sudo ./renew-ssl.sh
# Or force renewal
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

### Full health check

```bash
./scripts/health_check.sh
```

---

## Author

**Abdelrehman Elhaj** — [a.elhaj@proptech.sa](mailto:a.elhaj@proptech.sa)
GitHub: [AbdelrehmanElhaj](https://github.com/AbdelrehmanElhaj)

License: LGPL-3
