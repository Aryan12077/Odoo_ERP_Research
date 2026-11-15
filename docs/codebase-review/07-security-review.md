# 07 — Security Review

## 1. Threat Model & Security Posture

### Assets to Protect:
1. **Odoo ERP API Credentials & Service Tokens**: Access enables extracting sensitive organizational business data (payroll, accounts, vendor pricing, client details).
2. **PostgreSQL Target Data Warehouse Credentials**: Access allows reading, modifying, or dropping reporting tables.
3. **Enterprise Business & Financial Data**: Customer profiles, pricing models, general ledger journal entries, open debts, and supplier records.

### Trust Boundaries:
- **Boundary 1 (Local Environment to Odoo Cloud)**: Traversed over HTTPS (Port 443).
- **Boundary 2 (Local Environment to Remote Target Database)**: Traversed over TCP (Port 5433).
- **Boundary 3 (Local Filesystem)**: Environment files (`.env`), SQL dumps, scripts.

---

## 2. Security Findings Register

### SEC-01: Plain-Text Credentials in Repository Document Tree
- **Severity**: **Critical** | **Status**: Confirmed | **Confidence**: High
- **Evidence**: [`Documents/odoo credentials.txt`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/Documents/odoo%20credentials.txt) contains cleartext Odoo ERP URLs, database names, usernames, and unencrypted passwords.
- **Preconditions / Attack Surface**: Anyone with access to the local machine, filesystem backups, or a misconfigured Git push could read these credentials.
- **Potential Impact**: Full unauthorized API access to the production/cloud Odoo instance.
- **Existing Mitigating Controls**: `.gitignore` was updated to ignore `*.txt` and `Documents/`.
- **Recommended Remediation**:
  1. Immediately rotate the password/API key for user `odoodashboardsrdl@rdl.co.ke` inside Odoo ERP.
  2. Permanently delete [`Documents/odoo credentials.txt`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/Documents/odoo%20credentials.txt).
  3. Ensure no developer clones contain historical revisions of this file.
- **Verification Method**: Inspect `Documents/` to confirm deletion.

---

### SEC-02: Target Database Connection Configured with Superuser (`postgres`)
- **Severity**: **Medium** | **Status**: Confirmed | **Confidence**: High
- **Evidence**: [`.env:32`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/.env#L32) sets `TARGET_DB_USER=postgres`.
- **Preconditions / Attack Surface**: The ETL service connects as the PostgreSQL superuser rather than an application-scoped role.
- **Potential Impact**: If the ETL host is compromised, the attacker has superuser access to the entire PostgreSQL cluster, including system catalogs, foreign databases, and file-read functions (`pg_read_file`).
- **Existing Mitigating Controls**: Database is behind firewall on custom port 5433.
- **Recommended Remediation**: Create a dedicated least-privilege PostgreSQL user (e.g. `odoo_etl_user`) granted permissions strictly limited to schema `EBIZFRAME_BI`:
  ```sql
  CREATE USER odoo_etl_user WITH PASSWORD '...';
  GRANT USAGE ON SCHEMA "EBIZFRAME_BI" TO odoo_etl_user;
  GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA "EBIZFRAME_BI" TO odoo_etl_user;
  GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA "EBIZFRAME_BI" TO odoo_etl_user;
  ```
- **Verification Method**: Test running the pipeline with `TARGET_DB_USER=odoo_etl_user`.

---

### SEC-03: SQL Identifier Injection Risk via Python String Formatting
- **Severity**: **Medium** | **Status**: Confirmed | **Confidence**: High
- **Evidence**: [`db_loader.py:120`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/db_loader.py#L120) and [`db_loader.py:78`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/db_loader.py#L78):
  ```python
  f'TRUNCATE TABLE "{self.schema}"."{table_name}";'
  f'CALL "{self.schema}"."{proc}"(%s);'
  ```
- **Preconditions / Attack Surface**: Table names, schema names, and column headers are formatted directly into SQL strings using Python f-strings rather than `psycopg2.sql.Identifier`.
- **Potential Impact**: While table names currently originate from internal Python constants (`ext.target_table`), if input ever originates from untrusted CLI arguments or dynamic user input, it could permit SQL injection.
- **Existing Mitigating Controls**: Call sites use hardcoded table strings from extractor classes.
- **Recommended Remediation**: Refactor string interpolation to use `psycopg2.sql`:
  ```python
  from psycopg2 import sql
  query = sql.SQL('TRUNCATE TABLE {}.{}').format(
      sql.Identifier(self.schema),
      sql.Identifier(table_name)
  )
  cur.execute(query)
  ```
- **Verification Method**: Code inspection of `db_loader.py`.

---

### SEC-04: Optional SSL Disabling Flag in Configuration
- **Severity**: **Low** | **Status**: Confirmed | **Confidence**: High
- **Evidence**: [`config.py:28`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/config.py#L28) and [`.env:23`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/.env#L23) support `ODOO_VERIFY_SSL=False`.
- **Preconditions / Attack Surface**: If set to `False` in production, Python `requests` disables TLS certificate verification.
- **Potential Impact**: Exposure to Man-in-the-Middle (MITM) credential and payload interception.
- **Existing Mitigating Controls**: `.env` currently has `ODOO_VERIFY_SSL=True`.
- **Recommended Remediation**: Enforce `verify=True` in production environments, allowing `verify=False` only when an explicit `DEBUG=True` flag is present.
- **Verification Method**: Code review of `connector.py:43`.

---

## 3. Security Limitations & Exclusions

- **Network Penetration Testing**: Not performed. The remote database host (`161.118.176.229`) and Odoo SaaS infrastructure were not subjected to port scanning, vulnerability scans, or brute-force tests.
- **Dependency Vulnerabilities**: `psycopg2-binary 2.9.12` and `requests 2.33.1` are modern stable releases; however, a formal vulnerability scan (`pip-audit` or `safety`) has not been automated in a CI pipeline.

---

## 4. Document Links

- [Configuration, Integrations, and Data](05-configuration-integrations-and-data.md)
- [Reliability and Operations](08-reliability-and-operations.md)
- [Risks, Decisions, and Open Questions](10-risks-decisions-and-open-questions.md)

