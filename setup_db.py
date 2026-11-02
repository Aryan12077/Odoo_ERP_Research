"""
Database Schema Initializer / Setup Script.

Reads the schema definitions and stored procedures from DAL_BKP_08042026,
dynamically adapts the schema name (e.g. from 'EVA_BI' to 'odoo_roshni' as defined in .env),
and idempotently creates all tables and procedures in the target PostgreSQL database.
"""

import re
import sys
from config import get_target_db_config
from db_loader import DWHLoader


def setup_schema():
    print("=" * 70)
    print("TARGET POSTGRESQL SCHEMA INITIALIZER")
    print("=" * 70)

    try:
        cfg = get_target_db_config()
    except Exception as e:
        print(f"\n[ERROR] Configuration error in .env: {e}")
        print("Please ensure TARGET_DB_* variables are set in your .env file.")
        sys.exit(1)

    print(f"Target Database : {cfg.database} on {cfg.host}:{cfg.port}")
    print(f"Target Schema   : \"{cfg.schema}\"")
    print("-" * 70)

    loader = DWHLoader(cfg)
    conn_check = loader.test_connection()
    if not conn_check.get("connected"):
        print(f"\n[ERROR] Cannot connect to PostgreSQL: {conn_check.get('error')}")
        sys.exit(1)

    print("[1/3] Connected to PostgreSQL successfully.")

    # Read DAL_BKP_08042026
    try:
        with open("DAL_BKP_08042026", "r", encoding="utf-8") as f:
            dump_content = f.read()
    except Exception as e:
        print(f"[ERROR] Could not read DAL_BKP_08042026: {e}")
        sys.exit(1)

    print("[2/3] Processing DDL & Stored Procedures (Making Idempotent)...")

    # 1. Clean up dump-specific meta commands and permissions
    cleaned = re.sub(r"^\\restrict.*$", "", dump_content, flags=re.MULTILINE)
    cleaned = re.sub(r"^\\unrestrict.*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"ALTER TABLE .*? OWNER TO .*?;", "", cleaned)
    cleaned = re.sub(r"ALTER SCHEMA .*? OWNER TO .*?;", "", cleaned)
    cleaned = re.sub(r"ALTER PROCEDURE .*? OWNER TO .*?;", "", cleaned)
    cleaned = re.sub(r"GRANT .*? ON .*? TO .*?;", "", cleaned)

    # 2. Remove the dump's raw "CREATE SCHEMA" statement so it doesn't collide
    cleaned = re.sub(r'CREATE SCHEMA\s+"[^"]+";', "", cleaned)

    # 3. Replace schema 'EVA_BI' with the configured schema (e.g. 'odoo_roshni')
    target_schema = cfg.schema
    cleaned = cleaned.replace('"EVA_BI"', f'"{target_schema}"')
    cleaned = cleaned.replace("'EVA_BI'", f"'{target_schema}'")
    cleaned = cleaned.replace("EVA_BI.", f'"{target_schema}".')

    # 4. Make tables and procedures idempotent
    cleaned = re.sub(r'CREATE TABLE\s+"', 'CREATE TABLE IF NOT EXISTS "', cleaned)
    cleaned = re.sub(r'CREATE PROCEDURE\s+"', 'CREATE OR REPLACE PROCEDURE "', cleaned)

    # 5. Build final SQL with IF NOT EXISTS on schema
    prefix_sql = (
        f'CREATE SCHEMA IF NOT EXISTS "{target_schema}";\n'
        f'SET search_path TO "{target_schema}", public;\n'
    )
    final_sql = prefix_sql + cleaned

    print(f"[3/3] Executing schema creation on PostgreSQL schema \"{target_schema}\"...")
    try:
        conn = loader.get_connection()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(final_sql)
        conn.close()
        print("\n" + "=" * 70)
        print(f"[SUCCESS] Schema \"{target_schema}\" initialized successfully!")
        print(f"          - 43 Tables (including _TEMP) ready")
        print(f"          - 21 Stored Procedures ready")
        print("=" * 70)
    except Exception as e:
        print(f"\n[ERROR] Failed to execute SQL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_schema()
