"""
Currency Master Extractor
Target Table: "EVA_BI"."CURRENCY_MASTER"
Target Temp Table: "EVA_BI"."CURRENCY_MASTER_TEMP"
Source Model: "res.currency"
"""

from datetime import datetime
from typing import Any
from connector import OdooClient
from pipelines.base import (
    BaseExtractor,
    safe_num,
)


class CurrencyMasterExtractor(BaseExtractor):
    """
    Extracts currencies and rate factors from Odoo res.currency.
    """
    target_table = "CURRENCY_MASTER"
    procedure_name = "sp_update_currency_master"

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        currencies = client.search_read(
            model="res.currency",
            domain=[("active", "=", True)],
            fields=["id", "name", "symbol", "rate"]
        )

        rows = []
        snapshot = datetime.now()

        for cur in currencies:
            rate = safe_num(cur.get("rate"), 1.0)
            rows.append({
                "CURRENCY_CODE": cur["id"],
                "CURRENCY": cur.get("name") or "NA",
                "DIVIDEND": 1.0,
                "CONVERSION_FACTOR": rate,
                "DIVIDEND_ABBREVIATION": cur.get("name") or "NA",
                "CURRENCY_UNICHAR": cur.get("symbol") or "",
                "SNAPSHOT_DT": snapshot
            })

        return rows

