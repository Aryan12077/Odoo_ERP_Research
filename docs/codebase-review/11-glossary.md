# 11 — Glossary

## 1. Domain & ERP Terminology

| Term | Domain | Definition in this Codebase |
| :--- | :--- | :--- |
| **Odoo ERP** | Upstream System | Open-source enterprise resource planning platform providing CRM, accounting, inventory, sales, and manufacturing. |
| **JSON-RPC** | Protocol | Remote procedure call protocol encoded in JSON, used by `connector.py` over HTTPS `/jsonrpc` to execute Odoo model methods. |
| **`object.execute_kw`**| Odoo API | The core Odoo ORM dispatcher method that invokes Python methods (e.g., `search_read`, `search_count`) on Odoo models with positional and keyword arguments. |
| **`search_read`** | Odoo ORM | Combined Odoo method that searches for records matching a domain filter and returns a list of dictionaries populated with requested field values. |
| **Many2one (`m2o`)** | Odoo Field Type | A relational foreign key field in Odoo represented in API responses as a two-element array: `[id, "Display Name"]` (e.g., `[34979, "NAIVAS LTD"]`). |
| **`account.move`** | Odoo Model | The primary accounting journal entry header, representing customer invoices (`out_invoice`), credit notes (`out_refund`), vendor bills (`in_invoice`), and manual journal entries (`entry`). |
| **`account.move.line`** | Odoo Model | The granular accounting journal item (debit/credit lines). Forms the basis for General Ledger transactions, sales invoice lines, AR, and AP subledgers. |
| **`stock.quant`** | Odoo Model | The inventory quant table representing on-hand physical stock quantity located at a specific storage location or warehouse. |
| **`stock.picking`** | Odoo Model | Warehouse transfer/reception document representing Goods Receipt Notes (GRN), delivery orders, or internal movements. |
| **Anglo-Saxon Accounting**| Accounting Mode | Accounting policy in Odoo where Cost of Goods Sold (COGS) is recognized at the moment of customer delivery/invoicing rather than at vendor purchase. |
| **TIMS / CU Number** | Kenyan Tax System | Tax Invoice Management System (Kenya Revenue Authority Electronic Tax Register). Reflected in Odoo Kenyan localization fields (`cu_number`, `tims_invoice_no`). |

---

## 2. Data Warehouse & ETL Terminology

| Term | Domain | Definition in this Codebase |
| :--- | :--- | :--- |
| **`EBIZFRAME_BI`** | DWH Schema | The target PostgreSQL schema containing 22 production analytical tables, 21 staging tables, and 21 merge stored procedures. |
| **`Call ID`** | ETL Mechanism | A unique batch execution tag formatted as `CALL_{timestamp}_{uuid[:6]}` attached to all staging rows in `{TABLE}_TEMP` to isolate concurrently running batches. |
| **Staging Table (`_TEMP`)** | DWH Architecture | Intermediate PostgreSQL table mirroring the schema of the target analytical table without `SNAPSHOT_DT`, used to receive high-speed bulk inserts before merging. |
| **Idempotent Upsert** | Data Engineering | An operation where executing the ingestion multiple times produces the exact same end-state in the target table without generating duplicate records. |
| **`sp_update_{table}`** | Stored Procedure | A PL/pgSQL stored procedure in PostgreSQL that deletes existing target rows matching the business keys of the staging batch (`p_call_id`) and inserts fresh records. |
| **`execute_values`** | Performance Driver | High-performance bulk insertion method in `psycopg2.extras` that constructs multi-row `VALUES (...), (...)` clauses in batches of 1,000 rows. |
| **`SNAPSHOT_DT`** | Audit Column | Target DWH timestamp column defaulted to `now()`, recording the exact moment an analytical row was committed into the production table. |
| **Duration Buckets** | Financial Analytics | Accounts Receivable and Accounts Payable aging intervals: `DURATION1` (0–30 days), `DURATION2` (31–60 days), `DURATION3` (61–90 days), `DURATION4` (91–120 days), and `DURATION5` (>120 days). |

---

## 3. Project File & Codebase Acronyms

| Acronym / Symbol | Context | Description |
| :--- | :--- | :--- |
| **`DAL`** | Project History | Data Access Layer (referenced in backup dump `DAL_BKP_08042026`). |
| **`RDL`** | Tenant / Client | Roshni Distributors Ltd (the organization operating the target Odoo ERP instance). |
| **`REGISTRY`** | `run_pipeline.py` | Python dictionary registering task name strings to extractor classes. |
| **`DOMAINS`** | `run_pipeline.py` | Python dictionary grouping task names into domain bundles (`masters`, `sales`, `purchase`, `inventory`, `finance`). |
| **`BaseExtractor`** | `pipelines/base.py` | Abstract base class establishing the template method `run()` for all 18 table extractors. |

---

## 4. Document Links

- [Executive Summary](00-executive-summary.md)
- [System Context and Purpose](01-system-context-and-purpose.md)
- [Module and Interface Catalog](04-module-and-interface-catalog.md)
- [Developer KT Guide](09-developer-kt-guide.md)

