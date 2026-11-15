# 05 — Configuration, Integrations, and Data

## 1. Configuration Reference & Precedence

All configuration is governed by [`config.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/config.py) through `python-dotenv`. Values are loaded with the following precedence:
1. Active OS Environment Variables (Highest)
2. Local `.env` file in the project root directory
3. Default values hardcoded in `config.py` dataclasses (Lowest)

### Configuration Key Reference (Secret-Safe)

| Environment Variable | Dataclass Field | Type | Default Value | Description / Sensitivity |
| :--- | :--- | :---: | :---: | :--- |
| `ODOO_URL` | `OdooConfig.url` | `str` | `""` | Base HTTPS URL of Odoo ERP instance (e.g. `https://roshni13.odoo.com`). |
| `ODOO_DB` | `OdooConfig.db` | `str` | `""` | Odoo tenant database name. |
| `ODOO_USER` | `OdooConfig.username`| `str` | `""` | User email / login identity for API authentication. |
| `ODOO_PASSWORD` | `OdooConfig.secret` | `str` | `""` | **CRITICAL SECRET**: User password or API key. |
| `ODOO_TIMEOUT` | `OdooConfig.timeout` | `int` | `30` | HTTP request timeout in seconds. |
| `ODOO_VERIFY_SSL` | `OdooConfig.verify_ssl`| `bool` | `True` | Boolean toggle for TLS certificate verification. |
| `TARGET_DB_HOST` | `TargetDBConfig.host` | `str` | `""` | Target PostgreSQL hostname / IP address. |
| `TARGET_DB_PORT` | `TargetDBConfig.port` | `int` | `5432` | Target PostgreSQL port (falls back to 5432 if missing). |
| `TARGET_DB_NAME` | `TargetDBConfig.database`| `str` | `""` | Target database name. |
| `TARGET_DB_USER` | `TargetDBConfig.username`| `str` | `""` | Target database user identity. |
| `TARGET_DB_PASSWORD`| `TargetDBConfig.password`| `str` | `""` | **CRITICAL SECRET**: Target PostgreSQL password. |
| `TARGET_DB_SCHEMA` | `TargetDBConfig.schema` | `str` | `"EVA_BI"` | Target PostgreSQL schema name (e.g. `"EBIZFRAME_BI"`). |

> [!NOTE]
> The template file [`.env.example`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/.env.example) is committed to Git to document configuration keys with placeholder values (`ODOO_PASSWORD=your_api_key_or_password`). The actual `.env` is excluded via `.gitignore`.

---

## 2. External Integration Matrix

| Integration | Protocol / Transport | Auth Mechanism | Endpoints / Ports | Timeout / Retries | Error Handling |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Odoo Cloud ERP** | JSON-RPC 2.0 / XML-RPC over HTTPS | `common.authenticate` (User + API Key $\rightarrow$ UID) | `/jsonrpc`, `/xmlrpc/2/object` (Port 443) | Timeout: 30s (`ODOO_TIMEOUT`). No automatic retry loop. | Unpacks `result['error']` dict and raises standard Python exceptions. |
| **PostgreSQL DWH** | PostgreSQL Wire Protocol (TCP/IP) | Standard Password Auth (`md5` / `scram-sha-256`) | Remote port 5433 / 5432 | Connection timeout: default. Transaction blocks with rollback. | Rolls back active transaction on failure and surfaces SQL syntax/connection errors. |

---

## 3. Database & Schema Inventory

The target data warehouse schema (`EBIZFRAME_BI`) hosts **43 total tables** (22 production/analytical tables and 21 staging `_TEMP` tables) and **21 PL/pgSQL stored procedures**.

### Primary Target Analytical Tables:

```
EBIZFRAME_BI (Schema)
 ├── COMPANY_MASTER          (Company corporate hierarchy & base currencies)
 ├── BRANCH_MASTER           (Operating branches & locations)
 ├── CURRENCY_MASTER         (Exchange rates & conversion dividend factors)
 ├── CHART_OF_ACCOUNT        (Chart of accounts hierarchy)
 ├── ACCOUNT_TYPE            (Account type classifications & BS/PL flags)
 ├── CUSTOMER_MASTER         (Customer profiles, credit terms, addresses, salespersons)
 ├── SUPPLIER_MASTER         (Vendor master records & geographical metadata)
 ├── PRODUCT_MASTER          (63-column product catalog, 3-level categories, pricing)
 ├── SALES_DATA              (Granular invoice item lines, COGS, tax, sales executives)
 ├── MONTHLY_SALE            (Monthly customer invoice aggregations)
 ├── PURCHASE_DATA           (PO line subledgers, GRN receipts, vendor bill linkages)
 ├── MONTHLY_PURCHASE        (Monthly vendor billing aggregations)
 ├── INVENTORY_AGEING        (On-hand stock quants, standard valuation costs, warehouses)
 ├── TRANSACTION             (General Ledger journal entries, debits/credits)
 ├── ACCOUNT_RECEIVABLE      (Open AR customer balances & 5 aging duration buckets)
 ├── ACCOUNT_PAYABLE         (Open AP vendor balances & 5 aging duration buckets)
 ├── MONTHLY_COLLECTION      (Monthly customer cash collection receipts)
 ├── MONTHLY_PAYMENT         (Monthly vendor cash disbursements)
 ├── GEO_MASTER              (Warehouse, store, and branch geographical dimension)
 ├── ANALYSIS_CRITERIA       (Financial analysis codes and UOM criteria)
 ├── FISCAL_CALENDAR         (Fiscal year, calendar weeks, and date dimension)
 └── Data_Push_Agent_Log     (ETL execution timestamp and status audit trail)
```

### Staging Tables Pattern:
Every target table `{TABLE}` has an exact twin staging table `{TABLE}_TEMP`.
- `{TABLE}_TEMP` contains all business columns plus a required `"Call ID" character varying`.
- `{TABLE}_TEMP` does **not** contain `"SNAPSHOT_DT"`.
- Cleaned dynamically by stored procedures during key-based merge.

---

## 4. Data Lifecycle & Classification

| Data Category | Tables Involved | Classification | Retention & Purge Rules |
| :--- | :--- | :--- | :--- |
| **Master Dimensions** | `COMPANY_MASTER`, `BRANCH_MASTER`, `CUSTOMER_MASTER`, `SUPPLIER_MASTER`, `PRODUCT_MASTER` | Business Confidential | Upserted by primary code. Latest records retained. |
| **Customer Contact PII** | `CUSTOMER_MASTER.TELEPHONE`, `CUSTOMER_NAME` | Restricted PII | Extracted for billing delivery and reporting purposes. |
| **Transactional Subledgers** | `SALES_DATA`, `PURCHASE_DATA`, `TRANSACTION` | Highly Confidential Financial Data | Immutable historical subledgers. Deduplicated by invoice/PO/voucher number. |
| **Aging Balances** | `ACCOUNT_RECEIVABLE`, `ACCOUNT_PAYABLE` | Operational Financial Data | Overwritten with current open balances and updated duration buckets. |
| **Staging Batches** | `{TABLE}_TEMP` | Ephemeral Operational Data | Retains rows tagged by `Call ID`. Truncated when `--truncate` is passed. |

---

## 5. Document Links

- [Executive Summary](00-executive-summary.md)
- [Architecture and Components](02-architecture-and-components.md)
- [Module and Interface Catalog](04-module-and-interface-catalog.md)
- [Security Review](07-security-review.md)

