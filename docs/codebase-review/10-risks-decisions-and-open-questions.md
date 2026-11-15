# 10 — Risks, Decisions, and Open Questions

## 1. Risk Register

| ID | Risk Description | Likelihood | Impact | Severity | Evidence / Path | Mitigating Control / Strategy | Owner / Status |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| **R-01** | **Cleartext credentials exposed in repository files** | Medium | Critical | **Critical** | [`Documents/odoo credentials.txt`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/Documents/odoo%20credentials.txt) | Added `.gitignore` rule for `*.txt`. Permanent deletion and password rotation required. | Security Owner / Open |
| **R-02** | **Odoo JSON-RPC Timeout on Multi-Million Row Tables** | High | High | **High** | 1.62M Sales Lines and 5.26M GL Items in Odoo ERP (`connector.py:42`) | `--limit` flag exists. Need cursor pagination or date watermarking for incremental runs. | Data Engineer / In Progress |
| **R-03** | **ETL Database User Has PostgreSQL Superuser Privileges** | Medium | High | **Medium** | [`.env:32`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/.env#L32) (`TARGET_DB_USER=postgres`) | Provision dedicated `odoo_etl_user` granted only permissions on schema `EBIZFRAME_BI`. | DBA / Open |
| **R-04** | **Absence of Automated Regression Test Suite** | High | Medium | **Medium** | No `tests/` directory or `pytest.ini` present in codebase | Introduce pytest with mocked JSON-RPC fixtures for transformation edge cases. | Tech Lead / Open |
| **R-05** | **SQL String Interpolation for Table / Schema Names** | Low | High | **Medium** | [`db_loader.py:120`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/db_loader.py#L120) (`f'TRUNCATE TABLE "{self.schema}"."{table_name}"'`) | Use `psycopg2.sql.Identifier` for all dynamic table and schema interpolation. | Data Engineer / Open |
| **R-06** | **Unpinned Dependencies in Virtual Environment** | Medium | Low | **Low** | Absence of `requirements.txt` or `pyproject.toml` | Freeze verified dependencies into `requirements.txt` or `poetry.lock`. | DevOps / Open |
| **R-07** | **Memory Saturation on Client during Giant Batch Runs** | Medium | Medium | **Medium** | Loading 100,000+ dicts into client memory before bulk staging insert | Implement generator/streaming extraction that yields chunks of 5,000 directly to `execute_values`. | Data Engineer / Open |

---

## 2. Prioritized Recommendation Backlog

### Priority P0 (Urgent Material Security / Data-Integrity Issues)
- **REC-01: Rotate Production Credentials and Purge Historical Plaintext Files**
  - **Problem/Evidence**: [`Documents/odoo credentials.txt`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/Documents/odoo%20credentials.txt) contains active ERP login credentials.
  - **Expected Benefit**: Prevents unauthorized API compromise.
  - **Effort**: Low (1–2 hours).
  - **Dependencies**: ERP Admin access.
  - **Validation**: Verify that old credentials fail and new rotated credentials succeed.

### Priority P1 (High-Impact Correctness & Reliability Improvements)
- **REC-02: Implement Date Watermarking and Cursor Chunking for High-Volume Models**
  - **Problem/Evidence**: `account.move.line` contains 1.62M sales rows; full extractions time out over HTTP.
  - **Expected Benefit**: Enables reliable incremental daily extraction without timeouts or memory exhaustion.
  - **Effort**: Medium (1–2 days).
  - **Dependencies**: None.
  - **Validation**: Run extraction for a full calendar year in 10,000-row chunks.

- **REC-03: Restrict Database Connection to Least-Privilege Role**
  - **Problem/Evidence**: Currently connects to PostgreSQL as `postgres`.
  - **Expected Benefit**: Mitigates blast radius if application host is compromised.
  - **Effort**: Low (1 hour).
  - **Dependencies**: PostgreSQL DBA access.
  - **Validation**: Verify pipeline executes under `odoo_etl_user`.

### Priority P2 (Meaningful Maintainability Improvements)
- **REC-04: Establish Pytest Suite and Mock RPC Harness**
  - **Problem/Evidence**: Zero automated unit tests currently exist.
  - **Expected Benefit**: Enables safe continuous integration and refactoring.
  - **Effort**: Medium (2–3 days).
  - **Dependencies**: None.
  - **Validation**: Execute `pytest` in CI with 100% pass rate.

- **REC-05: Adopt `psycopg2.sql` Safe Identifier Formatting**
  - **Problem/Evidence**: `db_loader.py` formats schema and table names with f-strings.
  - **Expected Benefit**: Eliminates SQL injection surface on database operations.
  - **Effort**: Low (2–3 hours).
  - **Dependencies**: None.
  - **Validation**: Static code review and DWHLoader test suite.

### Priority P3 (Optional Refinements)
- **REC-06: Package into Standard Python Distribution**
  - **Problem/Evidence**: Unpackaged repository with loose scripts.
  - **Expected Benefit**: Installable via `pip install -e .` with console entry point `odoo-etl`.
  - **Effort**: Low (4 hours).
  - **Dependencies**: None.

---

## 3. Open Questions for Domain Owners

| Question | Why It Matters | Evidence Sought | Suggested Role | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Q-01: What is the official historical cutoff date for analytics?** | Querying from 2018 onwards involves millions of records; defining a historical cutoff (e.g., 2024-01-01) drastically accelerates daily ingestion. | Business reporting SLA or CFO policy. | CFO / Head of BI | **Open** |
| **Q-02: Are warehouses (`stock.warehouse`) considered distinct branches?** | In `BRANCH_MASTER`, companies are currently mapped 1:1 to branches. If the 5 warehouses represent branches, `BRANCH_MASTER` should reflect them. | Branch definitions in existing reports. | Operations Director | **Open** |
| **Q-03: Should COGS be calculated from landed costs or standard costing?** | Currently `COGS_USD` is defaulted to 0.0 unless landed cost valuation layers are enabled. | Financial accounting preference for COGS recognition. | Lead Accountant | **Open** |
| **Q-04: What is the preferred cleanup policy for staging tables (`{TABLE}_TEMP`)?** | Staging rows accumulate tagged with `Call ID`. Should old `Call ID`s be purged weekly via vacuum? | Database disk capacity and audit policies. | Database Administrator | **Open** |

---

## 4. Architectural Decision Log (ADR Summary)

- **ADR-01: JSON-RPC Chosen as Primary Transport over XML-RPC**
  - *Context*: Odoo supports both XML-RPC and JSON-RPC.
  - *Decision*: Adopt JSON-RPC (`/jsonrpc`) for faster serialization, lower parsing latency, and simpler native dictionary handling in Python.
  - *Status*: Verified in `connector.py`.
- **ADR-02: Staging-and-Merge Pattern over Direct Target Writes**
  - *Context*: Partial failures during long API extractions could corrupt target reporting tables.
  - *Decision*: Ingest all rows into isolated staging tables tagged with `Call ID`, followed by atomic stored procedure upsert.
  - *Status*: Verified in `db_loader.py` and `setup_db.py`.
- **ADR-03: Derived Standard Costing for Restricted Quant Valuation**
  - *Context*: API user lacks permissions to read `stock.quant.value`.
  - *Decision*: Read `product.product.standard_price` and multiply by `quantity` to derive inventory valuation.
  - *Status*: Verified in `pipelines/inventory/inventory_ageing.py:85-115`.
- **ADR-04: Stripping `SNAPSHOT_DT` in Staging Tuples**
  - *Context*: Target tables feature `SNAPSHOT_DT DEFAULT now()`, but staging tables do not have the column.
  - *Decision*: Programmatically strip `SNAPSHOT_DT` before bulk inserting into `{TABLE}_TEMP`.
  - *Status*: Verified in `db_loader.py:108`.

---

## 5. Document Links

- [Executive Summary](00-executive-summary.md)
- [Security Review](07-security-review.md)
- [Reliability and Operations](08-reliability-and-operations.md)
- [Glossary](11-glossary.md)

