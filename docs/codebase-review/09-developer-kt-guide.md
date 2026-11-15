# 09 — Developer Knowledge Transfer (KT) Guide

## 1. 30-Minute Onboarding Orientation Path

Welcome to the **Odoo Data Extraction & Analytics Pipeline** codebase. This guide enables a newly onboarded engineer to configure a local environment, understand the execution path, run safe dry-run extractions, and add new table extractors within 30 minutes.

### Read First:
1. [`00-executive-summary.md`](00-executive-summary.md) — 5-minute architecture and data flow overview.
2. [`01-system-context-and-purpose.md`](01-system-context-and-purpose.md) — Understand Odoo upstream and PostgreSQL downstream context.
3. [`04-module-and-interface-catalog.md`](04-module-and-interface-catalog.md) — Reference for classes and domain extractors.

---

## 2. Local Environment Setup

### Prerequisites:
- Python 3.11.x installed (`python --version`)
- Access to an Odoo ERP instance (URL, Database Name, User Email, and API Key)
- Access to a target PostgreSQL database (Host, Port, Database, User, Password)

### Step 1: Clone Repository & Create Virtual Environment
```powershell
# Open terminal in project root
cd "D:\ARYAN GUPTA OLD LAPTOP BACKUP\PROJECTS\ODOO ERP Research"

# Create a clean virtual environment (if not already present)
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate
```

### Step 2: Install Core Dependencies
```powershell
pip install requests psycopg2-binary python-dotenv
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your actual credentials:
```powershell
Copy-Item .env.example .env
```
Ensure your `.env` contains:
```env
ODOO_URL=https://roshni13.odoo.com
ODOO_DB=hyperthinkkenya-roshni-v13-main-4074481
ODOO_USER=your_odoo_user@company.com
ODOO_PASSWORD=your_odoo_api_key
ODOO_TIMEOUT=30
ODOO_VERIFY_SSL=True

TARGET_DB_HOST=161.118.176.229
TARGET_DB_PORT=5433
TARGET_DB_NAME=your_db_name
TARGET_DB_USER=your_db_user
TARGET_DB_PASSWORD=your_db_password
TARGET_DB_SCHEMA=EBIZFRAME_BI
```

### Step 4: Verify Connectivity
Run the test script in `MISC/`:
```powershell
python MISC/test_db_conn.py
```
Expected output:
```text
Loaded .env from: D:\...\.env
Target DB: Host=161.118.176.229, DB=..., User=..., Schema=EBIZFRAME_BI
Testing port 5433...
  [SUCCESS] Connected to port 5433!
```

---

## 3. Safe Execution Guide (How to Run Pipelines)

### A. Dry Run Mode (Safe: No Database Writes)
Always start with dry-run mode when developing or testing. It extracts records from Odoo and prints timing/row counts to console without touching PostgreSQL:
```powershell
# Run a single extractor with a 5-record limit:
python run_pipeline.py --extractor company_master --limit 5

# Run an entire domain dry-run:
python run_pipeline.py --domain sales --limit 10
```

### B. Ingest Mode (Extract & Load to PostgreSQL)
When ready to write to the target data warehouse:
```powershell
# Ingest all domains:
python run_pipeline.py --domain all --load

# Ingest a specific domain:
python run_pipeline.py --domain finance --load
```

### C. Truncate-and-Reload Mode
When you need to empty target tables before inserting fresh data:
```powershell
python run_pipeline.py --domain all --truncate
```

---

## 4. How to Make a Typical Change

### Scenario A: Adding a New Field to an Existing Extractor
Suppose you want to add `customer_category` to `CUSTOMER_MASTER`:
1. Check Odoo column metadata in `odoo_table_column_metadata.csv` to find the exact source field name (e.g. `category_id`).
2. Open [`pipelines/masters/customer.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/customer.py).
3. Add the field to the `fields` list in `extract()`:
   ```python
   fields = ["id", "name", "user_id", "category_id", ...]
   ```
4. Map the field in the dictionary:
   ```python
   "CATEGORY": get_m2o_name(p.get("category_id"), "General"),
   ```
5. Test the extraction with dry-run:
   ```powershell
   python run_pipeline.py --extractor customer_master --limit 5
   ```

### Scenario B: Adding a Completely New Table Extractor
Suppose you want to extract a new table `TAX_MASTER` from Odoo model `account.tax`:
1. Create a new file `pipelines/masters/tax.py`.
2. Inherit from `BaseExtractor` (`from pipelines.base import BaseExtractor`):
   ```python
   from datetime import datetime
   from pipelines.base import BaseExtractor, safe_num

   class TaxMasterExtractor(BaseExtractor):
       target_table = "TAX_MASTER"
       procedure_name = "sp_update_tax_master"

       def extract(self, client):
           taxes = client.search_read("account.tax", fields=["id", "name", "amount", "type_tax_use"])
           rows = []
           snapshot = datetime.now()
           for t in taxes:
               rows.append({
                   "TAX_ID": t["id"],
                   "TAX_NAME": t["name"],
                   "RATE": safe_num(t.get("amount")),
                   "TYPE": t.get("type_tax_use"),
                   "SNAPSHOT_DT": snapshot
               })
           return rows
   ```
3. Register the new extractor in [`run_pipeline.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/run_pipeline.py):
   ```python
   from pipelines.masters.tax import TaxMasterExtractor
   REGISTRY["tax_master"] = TaxMasterExtractor
   DOMAINS["masters"].append("tax_master")
   ```
4. Ensure the target table `TAX_MASTER`, staging table `TAX_MASTER_TEMP`, and procedure `sp_update_tax_master` exist in PostgreSQL.

---

## 5. Common Pitfalls & Developer Warnings

> [!WARNING]
> **1. Never Query `stock.quant.value` or `res.partner.credit_limit` Directly**
> In Odoo, these fields are restricted to administrator security groups (`base.group_erp_manager`). Querying them will throw `AccessError` for standard API integration users. Calculate inventory valuation using `product.product.standard_price * quantity`.

> [!WARNING]
> **2. Never Run Unfiltered Extractions on `account.move.line` Without Date Limits**
> There are over 1.62 million sales lines and 5.26 million GL lines in Odoo. A raw query without limits will exceed Odoo's 30-second HTTP timeout. Always use indexed filters (`parent_state = 'posted'`, `date >= '...'`).

> [!CAUTION]
> **3. Staging Tables Do NOT Have `SNAPSHOT_DT`**
> Production tables have `"SNAPSHOT_DT" timestamp DEFAULT now()`, but `{TABLE}_TEMP` tables do not. `db_loader.py` automatically strips `SNAPSHOT_DT` before bulk inserting into staging. Do not add `SNAPSHOT_DT` to staging DDL.

---

## 6. Document Links

- [Executive Summary](00-executive-summary.md)
- [Module and Interface Catalog](04-module-and-interface-catalog.md)
- [Testing, Quality, and Build](06-testing-quality-and-build.md)
- [Glossary](11-glossary.md)

