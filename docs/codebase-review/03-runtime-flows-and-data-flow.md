# 03 — Runtime Flows and Data Flow

## 1. Primary Execution Flow: Extractor Pipeline (`--load`)

This flow describes the execution path when a user or scheduler runs `python run_pipeline.py --domain <name> --load`.

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Operator as CLI / Scheduler
    participant Runner as run_pipeline.py
    participant Client as OdooClient (connector.py)
    participant Odoo as Odoo ERP API (/jsonrpc)
    participant Extractor as Domain Extractor (pipelines/*)
    participant Loader as DWHLoader (db_loader.py)
    participant Postgres as PostgreSQL Target DWH

    Operator->>Runner: python run_pipeline.py --domain sales --load
    Runner->>Client: authenticate()
    Client->>Odoo: POST /jsonrpc (common.authenticate)
    Odoo-->>Client: uid: 26
    Client-->>Runner: Authenticated

    Runner->>Loader: test_connection()
    Loader->>Postgres: SELECT version(), EXISTS(schema)
    Postgres-->>Loader: Connected & Schema Exists
    Loader-->>Runner: Ready

    loop For each Task in Domain (e.g. SALES_DATA)
        Runner->>Extractor: ext.run(client, loader)
        Extractor->>Client: search_read("account.move.line", domain, fields, limit)
        Client->>Odoo: POST /jsonrpc (object.execute_kw -> search_read)
        Odoo-->>Client: list[raw_dict]
        Client-->>Extractor: raw_records

        Note over Extractor: Normalization & Enrichment<br/>Batch lookup parent moves (salesperson)<br/>Type casting & bracket extraction

        Extractor->>Loader: load_staging_and_merge("SALES_DATA", records)
        Note over Loader: Generate unique Call ID<br/>Strip SNAPSHOT_DT for temp table
        Loader->>Postgres: execute_values -> INSERT INTO "SALES_DATA_TEMP"
        Loader->>Postgres: CALL sp_update_sales_data(p_call_id)
        
        Note over Postgres: Stored Procedure execution:<br/>1. DELETE FROM SALES_DATA USING SALES_DATA_TEMP<br/>   WHERE keys match AND Call ID = p_call_id<br/>2. INSERT INTO SALES_DATA SELECT ... FROM TEMP
        
        Postgres-->>Loader: Procedure Completed
        Loader-->>Extractor: {status: SUCCESS, rows: 5000}
        Extractor-->>Runner: Task Execution Summary
    end

    Runner-->>Operator: JSON Execution Summary & Total Elapsed Time
```

### Step-by-Step Execution Narrative
1. **CLI Invocation**: `run_pipeline.py:main()` parses command-line arguments using `argparse`.
2. **Authentication**: `OdooClient.authenticate()` calls Odoo's `common.authenticate` service with `ODOO_DB`, `ODOO_USER`, and `ODOO_PASSWORD`/API key (`connector.py:59-74`).
3. **Target Connection Check**: If `--load` is enabled, `DWHLoader.test_connection()` verifies connectivity and validates that `TARGET_DB_SCHEMA` exists (`db_loader.py:42-68`).
4. **Task Iteration**: The runner iterates through task names registered in the specified domain.
5. **Data Extraction**:
   - The extractor calls `client.search_read(model, domain, fields, limit, order)`.
   - The query filters by indexed fields (e.g., `parent_state = 'posted'`, `display_type = 'product'`).
   - If auxiliary data is needed (e.g. Salesperson on invoices, GRN pickings on purchase orders), secondary batch lookups query related models in chunks of 500 (`sales_data.py:90-105`).
6. **Data Transformation & Normalization**:
   - Many2one arrays `[id, "Display Name"]` are unwrapped via `get_m2o_id()` and `get_m2o_name()`.
   - Product SKU codes are extracted from bracketed strings (e.g., `"[H1041] HARIBO"` $\rightarrow$ `"H1041"`).
   - Numeric quantities and amounts are normalized; refund records are multiplied by `-1.0`.
   - Dates are parsed and standardized into PostgreSQL timestamp strings (`YYYY-MM-DD HH:MM:SS`).
7. **Staging Table Insertion**:
   - `DWHLoader.load_staging_and_merge()` generates a unique `call_id = f"CALL_{timestamp}_{uuid[:6]}"`.
   - `SNAPSHOT_DT` is omitted from tuple bindings.
   - Rows are streamed into `"{schema}"."{table}_TEMP"` via `psycopg2.extras.execute_values` in batches of 1,000 (`db_loader.py:128-133`).
8. **Stored Procedure Merge**:
   - `CALL "{schema}"."{procedure_name}"(p_call_id)` is invoked inside a database transaction block (`db_loader.py:136-138`).
   - The procedure performs a key-based `DELETE` on the production table matching the staging keys for `p_call_id`, followed by an `INSERT` of the staged rows.
   - The transaction commits atomically. If any error occurs, `conn.rollback()` ensures no corrupted state persists.

---

## 2. Target Database Schema Initialization Flow (`setup_db.py`)

### Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Admin / Setup Script
    participant Setup as setup_db.py
    participant File as DAL_BKP_08042026
    participant Loader as DWHLoader
    participant Postgres as PostgreSQL Target Database

    Operator->>Setup: python setup_db.py
    Setup->>Loader: test_connection()
    Loader->>Postgres: SELECT version()
    Postgres-->>Setup: Connected

    Setup->>File: Read SQL Dump content
    File-->>Setup: Raw SQL DDL & PL/pgSQL procedures

    Note over Setup: DDL Sanitization & Idempotency:<br/>1. Strip \restrict and \unrestrict meta commands<br/>2. Strip OWNER TO and GRANT statements<br/>3. Strip hardcoded CREATE SCHEMA EVA_BI<br/>4. Regex replace EVA_BI -> Target Schema (.env)<br/>5. Make CREATE TABLE IF NOT EXISTS<br/>6. Make CREATE OR REPLACE PROCEDURE

    Setup->>Postgres: CREATE SCHEMA IF NOT EXISTS "{schema}"
    Setup->>Postgres: SET search_path TO "{schema}"
    Setup->>Postgres: Execute sanitized DDL (43 Tables)
    Setup->>Postgres: Execute sanitized Procedures (21 SPs)
    Postgres-->>Setup: Execution Completed
    Setup-->>Operator: Schema Successfully Initialized (43 Tables, 21 Procedures)
```

---

## 3. Truncate-and-Load Flow (`--truncate`)

When the operator specifies `--truncate`:
1. `run_pipeline.py` automatically enables `--load = True`.
2. For each extractor task to be executed, before extraction begins, the runner triggers `loader.truncate_table(ext.target_table)`.
3. In PostgreSQL, `TRUNCATE TABLE "{schema}"."{table}";` and `TRUNCATE TABLE "{schema}"."{table}_TEMP";` are executed atomically.
4. Extraction proceeds, and the fresh dataset is inserted into the empty table.
5. This ensures that any records previously present that no longer exist in Odoo (deletions / cancellations) are purged.

---

## 4. Data Transformation Pipeline & Type Mapping

| Odoo Source Field Type | Transformation / Helper | Target PostgreSQL Type | Example Input | Normalized Output |
| :--- | :--- | :--- | :--- | :--- |
| `Many2one` (Array) | `get_m2o_id(val)` | `integer` / `varchar` | `[34979, "NAIVAS LTD"]` | `34979` |
| `Many2one` (Array) | `get_m2o_name(val, default)`| `varchar` | `[9, "Kizito"]` | `"Kizito"` |
| `Char` (Bracketed SKU) | Custom bracket parsing | `varchar` | `"[H1041] HARIBO"` | `"H1041"` |
| `Float` / `Monetary` | `safe_num(val, default=0.0)`| `numeric` | `None` or `"3287.76"` | `3287.76` |
| `Date` / `Datetime` | `parse_date(val)` | `timestamp` | `"2026-10-31 04:38:27"` | `"2026-10-31 04:38:27"` |
| `Selection` (Refunds) | `* -1.0 if refund else 1.0` | `numeric` | Subtotal `100.0` (out_refund) | `-100.0` |
| `Integer` (Company/Branch) | `pad_code(val, width=2)` | `varchar` | `1` | `"01"` |
| Automatic Audit | Database default | `timestamp` | Database `now()` | `2026-11-02 15:30:21` |

---

## 5. Document Links

- [System Context and Purpose](01-system-context-and-purpose.md)
- [Architecture and Components](02-architecture-and-components.md)
- [Module and Interface Catalog](04-module-and-interface-catalog.md)
- [Reliability and Operations](08-reliability-and-operations.md)

