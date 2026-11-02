"""
Database Loader Module for Target PostgreSQL Data Warehouse (EVA_BI).

Handles:
- Connecting to Target PostgreSQL database
- Generating unique execution batch Call IDs
- Bulk inserting staging records into {TABLE}_TEMP
- Invoking the corresponding stored procedure sp_update_{table}(p_call_id)
- Transaction management (commit/rollback)
"""

import uuid
from datetime import datetime
from typing import Any, Optional
import psycopg2
from psycopg2 import extras

from config import TargetDBConfig, get_target_db_config


class DWHLoader:
    """
    Manages loading transformed Odoo data into the target EVA_BI schema.
    """

    def __init__(self, target_config: Optional[TargetDBConfig] = None):
        self.config = target_config or get_target_db_config()
        self.schema = self.config.schema

    def get_connection(self):
        """
        Creates and returns a new PostgreSQL database connection.
        """
        return psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.database,
            user=self.config.username,
            password=self.config.password
        )

    def test_connection(self) -> dict:
        """
        Tests connectivity to the target database and checks for the schema.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()[0]

                    cur.execute(
                        "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = %s);",
                        (self.schema,)
                    )
                    schema_exists = cur.fetchone()[0]

            return {
                "connected": True,
                "version": version,
                "schema": self.schema,
                "schema_exists": schema_exists
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

    def load_staging_and_merge(
        self,
        table_name: str,
        records: list[dict[str, Any]],
        procedure_name: Optional[str] = None
    ) -> dict:
        """
        Inserts records into {table_name}_TEMP with a generated Call ID,
        then calls the stored procedure sp_update_{table}(p_call_id) to merge.

        Parameters
        ----------
        table_name : str
            Base target table name (e.g. "COMPANY_MASTER", "SALES_DATA").
        records : list[dict]
            Transformed rows matching target schema columns.
        procedure_name : str, optional
            Stored procedure name. Defaults to 'sp_update_{table_name.lower()}'.

        Returns
        -------
        dict
            Execution summary (call_id, rows_inserted, procedure, status).
        """
        if not records:
            return {
                "table": table_name,
                "call_id": None,
                "rows_inserted": 0,
                "status": "SKIPPED (Empty dataset)"
            }

        proc = procedure_name or f"sp_update_{table_name.lower()}"
        call_id = f"CALL_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        staging_table = f"{table_name}_TEMP"

        # Determine all columns from the first record + ensure 'Call ID' is included
        # Filter out 'SNAPSHOT_DT' if present, as the TEMP table does not have SNAPSHOT_DT
        sample_keys = [k for k in records[0].keys() if k != "SNAPSHOT_DT" and k != "Call ID"]
        columns = ["Call ID"] + sample_keys

        # Prepare values tuples
        values_to_insert = []
        for r in records:
            row_tuple = [call_id] + [r.get(col) for col in sample_keys]
            values_to_insert.append(tuple(row_tuple))

        # Build quoted column names for PostgreSQL
        quoted_cols = ", ".join([f'"{c}"' for c in columns])
        insert_query = (
            f'INSERT INTO "{self.schema}"."{staging_table}" ({quoted_cols}) VALUES %s'
        )

        conn = self.get_connection()
        try:
            with conn:
                with conn.cursor() as cur:
                    # 1. Bulk insert into staging table
                    extras.execute_values(
                        cur,
                        insert_query,
                        values_to_insert,
                        page_size=1000
                    )

                    # 2. Invoke merge stored procedure
                    call_proc_query = f'CALL "{self.schema}"."{proc}"(%s);'
                    cur.execute(call_proc_query, (call_id,))

            return {
                "table": table_name,
                "call_id": call_id,
                "rows_inserted": len(records),
                "procedure": proc,
                "status": "SUCCESS"
            }

        except Exception as e:
            conn.rollback()
            raise RuntimeError(
                f"Failed to load {table_name} via {staging_table} / {proc}: {e}"
            ) from e
        finally:
            conn.close()

