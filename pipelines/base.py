"""
Base Extractor and Common Utility Functions for Odoo ETL Pipelines.
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Any, Optional
import time

from connector import OdooClient
from db_loader import DWHLoader


class BaseExtractor(ABC):
    """
    Abstract Base Class for all domain extractors.
    """

    target_table: str = ""
    procedure_name: Optional[str] = None

    @abstractmethod
    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        """
        Pulls data from Odoo and returns a list of dictionaries matching
        the target table's schema.
        """
        pass

    def run(
        self,
        client: OdooClient,
        loader: Optional[DWHLoader] = None
    ) -> dict[str, Any]:
        """
        Executes the extraction and optionally loads data into the target DWH.
        """
        start_time = time.time()
        table = self.target_table or self.__class__.__name__

        # 1. Extract from Odoo
        records = self.extract(client)
        elapsed = round(time.time() - start_time, 2)

        result = {
            "table": table,
            "extracted_count": len(records),
            "extraction_duration_sec": elapsed,
            "status": "EXTRACTED"
        }

        # 2. Load into Target Database if loader is provided
        if loader and records:
            load_result = loader.load_staging_and_merge(
                table_name=table,
                records=records,
                procedure_name=self.procedure_name
            )
            result.update({
                "call_id": load_result.get("call_id"),
                "rows_loaded": load_result.get("rows_inserted"),
                "procedure": load_result.get("procedure"),
                "status": load_result.get("status")
            })
        elif loader and not records:
            result["status"] = "SKIPPED (No data extracted)"

        return result


# =====================================================================
# Odoo Field Parsing Helpers
# =====================================================================

def get_m2o_id(val: Any) -> Optional[int]:
    """
    Safely extracts the ID from an Odoo Many2one field [id, name].
    Returns None if empty or False.
    """
    if isinstance(val, (list, tuple)) and len(val) >= 1:
        return val[0]
    return None


def get_m2o_name(val: Any, default: Optional[str] = None) -> Optional[str]:
    """
    Safely extracts the display name from an Odoo Many2one field [id, name].
    Returns default if empty or False.
    """
    if isinstance(val, (list, tuple)) and len(val) >= 2:
        return str(val[1])
    return default


def pad_code(val: Any, length: int = 2) -> str:
    """
    Left-pads a code with zeros to standard length (e.g. 1 -> '01').
    """
    if val is None or val is False:
        return "00"
    return str(val).zfill(length)


def parse_date(val: Any) -> Optional[str]:
    """
    Validates and formats an Odoo date/datetime string to ISO format.
    """
    if not val or val is False:
        return None
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return str(val)


def safe_num(val: Any, default: float = 0.0) -> float:
    """
    Converts a value to float safely.
    """
    if val is None or val is False:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

