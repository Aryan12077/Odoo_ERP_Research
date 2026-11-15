# 08 — Reliability and Operations

## 1. Reliability Architecture & Idempotency Analysis

The pipeline's primary operational reliability mechanism is its **Two-Phase Staging & Stored Procedure Merge Architecture**.

```
[Extract Phase] ────────► [Staging Phase] ────────► [Merge Phase]
Fetch from Odoo           Bulk insert into          Atomic Procedure
JSON-RPC (Memory)         {TABLE}_TEMP              Key-based Delete
                          Tagged with 'Call ID'     Followed by Insert
```

### Key Reliability Characteristics:
1. **Zero Corrupted Ingestions**: If an extractor crashes midway or the Odoo connection drops while fetching records, no partial records enter production tables because the stored procedure is never invoked.
2. **Transaction Rollback Protection**: In `db_loader.py:125-151`, all database operations execute inside a `with conn:` context manager. If `extras.execute_values` or `CALL sp_update_*` raises an exception, psycopg2 automatically triggers `conn.rollback()`.
3. **Audit Trail**: Every execution can log directly to `Data_Push_Agent_Log` with `Log_id`, `Log_Procedure`, `Log_Status`, and `Log_Time`.

---

## 2. Failure Mode and Effects Analysis (FMEA)

| Failure Mode | Root Cause | Observable Symptom | Impact | System Recovery / Remediation |
| :--- | :--- | :--- | :--- | :--- |
| **HTTP Read Timeout** | Fetching unbounded records on large tables (>50k rows) in single RPC call. | `requests.exceptions.ReadTimeout: HTTPSConnectionPool(...)` | Task fails; pipeline halts. Production table untouched. | Re-run with `--limit <N>` or add date watermarking (`date >= '2026-01-01'`). |
| **PostgreSQL Auth Failure** | Incorrect database credentials or network access restriction. | `psycopg2.OperationalError: FATAL: password authentication failed` | Cannot load data into DWH. | Validate `TARGET_DB_*` credentials in `.env` using `MISC/test_db_conn.py`. |
| **Missing Schema in Target DB** | Connecting to clean DB without initializing DDL first. | `psycopg2.errors.UndefinedTable: relation "{TABLE}_TEMP" does not exist` | Merge procedure fails. | Run `python setup_db.py` once to provision all 43 tables and 21 procedures. |
| **Odoo Access Restriction** | API user lacks permissions for specific models (e.g. `stock.quant.value`). | `odoo.exceptions.AccessError: You do not have access rights...` | Task terminates immediately. | Exclude restricted fields; derive values via permitted joins (`product.product.standard_price`). |
| **Network Interruption during Staging** | Dropped TCP socket during `execute_values`. | `psycopg2.OperationalError: server closed the connection unexpectedly` | Transaction rolled back automatically. | Ensure database firewall has stable keep-alive; rerun task. |

---

## 3. High-Volume Memory & Sizing Considerations

A live database audit established the following total record counts in Odoo ERP:
- **Sales Items (`account.move.line`)**: **1,620,084 records**
- **General Ledger Items (`account.move.line`)**: **5,262,788 records**
- **Purchase Lines (`purchase.order.line`)**: **17,963 records**

### Sizing and Memory Risks:
1. **Client Memory Exhaustion**: Loading 1.62 million Python dictionaries containing 12 fields into client RAM requires approximately **2.5 to 3.5 GB of memory**.
2. **Odoo Server Memory Limits**: Odoo's worker processes will terminate or return an HTTP 504 Gateway Timeout if forced to serialize millions of relational records into JSON-RPC responses.

### Recommended Operational Sizing Guidelines:
- **Default Extraction Batch Size**: Recommended at **10,000 to 25,000 records** per run when pulling full historical data.
- **Incremental Extraction**: Always pass date constraints for daily/weekly scheduled runs:
  ```python
  domain.append(('date', '>=', last_execution_watermark))
  ```

---

## 4. Operational Monitoring & Runbooks

### Runbook 1: Daily Scheduled Ingestion
To configure an automated daily ingestion via Linux cron or Windows Task Scheduler:
```powershell
# 1. Activate Virtual Environment
.\venv\Scripts\Activate.ps1

# 2. Run All Extractors and Load to PostgreSQL
python run_pipeline.py --domain all --load >> logs\daily_pipeline.log 2>&1
```

### Runbook 2: Full Data Warehouse Reset & Reload
To wipe all historical tables and ingest a clean baseline:
```powershell
python run_pipeline.py --domain all --truncate
```

### Runbook 3: Monitoring Row Counts
To verify live counts across all 18 tables in PostgreSQL:
```powershell
python MISC/check_counts.py
```

---

## 5. Document Links

- [Runtime Flows and Data Flow](03-runtime-flows-and-data-flow.md)
- [Configuration, Integrations, and Data](05-configuration-integrations-and-data.md)
- [Security Review](07-security-review.md)
- [Developer KT Guide](09-developer-kt-guide.md)

