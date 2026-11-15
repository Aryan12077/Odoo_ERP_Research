"""
Analysis Criteria Extractor
Target Table: "EVA_BI"."ANALYSIS_CRITERIA"
Target Temp Table: "EVA_BI"."ANALYSIS_CRITERIA_TEMP"
Source Model: "res.currency" + Standard BI scaling units

Columns:
- Analysis Code (numeric)
- Analysis Criteria (varchar)
- Analysis Type (varchar)
- Active (numeric)
- Target Available (numeric)
- Currency Code (integer)
- Currency (varchar)
- Currency Unichar (varchar)
- Code (numeric)
- Unit (varchar)
- Dividend (numeric)
- Short Form (varchar)
- Long Form (varchar)
- Long Text (varchar)
- UOM (varchar)
- SNAPSHOT_DT (timestamp)
"""

from datetime import datetime
from typing import Any, Optional
from connector import OdooClient
from pipelines.base import BaseExtractor


class AnalysisCriteriaExtractor(BaseExtractor):
    """
    Extracts and synchronizes BI analysis scaling criteria, currency units, and display rules.
    """
    target_table = "ANALYSIS_CRITERIA"
    procedure_name = "sp_update_analysis_criteria"

    def __init__(self, domain: Optional[list] = None):
        self.custom_domain = domain

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        # Fetch active currencies from Odoo
        curr_domain = [("active", "=", True)]
        if self.custom_domain:
            curr_domain.extend(self.custom_domain)

        currencies = client.search_read(
            model="res.currency",
            domain=curr_domain,
            fields=["id", "name", "symbol"]
        )

        if not currencies:
            currencies = [{"id": 1, "name": "KES", "symbol": "KSh"}]

        # Standard scaling units for BI reporting
        scaling_definitions = [
            {
                "criteria": "Actual",
                "type": "Amount",
                "unit": "Actual",
                "dividend": 1.0,
                "short": "Act",
                "long": "Actual",
                "text": "Actual Values"
            },
            {
                "criteria": "Thousands",
                "type": "Amount",
                "unit": "Thousands",
                "dividend": 1000.0,
                "short": "K",
                "long": "Thousands",
                "text": "In Thousands"
            },
            {
                "criteria": "Millions",
                "type": "Amount",
                "unit": "Millions",
                "dividend": 1000000.0,
                "short": "M",
                "long": "Millions",
                "text": "In Millions"
            },
            {
                "criteria": "Quantity",
                "type": "Quantity",
                "unit": "Units",
                "dividend": 1.0,
                "short": "Qty",
                "long": "Units",
                "text": "In Units"
            }
        ]

        rows = []
        snapshot = datetime.now()
        analysis_code = 1

        for c in currencies:
            c_id = c["id"]
            c_name = c.get("name") or "KES"
            c_symbol = c.get("symbol") or c_name

            for scale in scaling_definitions:
                rows.append({
                    "Analysis Code": analysis_code,
                    "Analysis Criteria": f"{scale['criteria']} ({c_name})",
                    "Analysis Type": scale["type"],
                    "Active": 1,
                    "Target Available": 1,
                    "Currency Code": c_id,
                    "Currency": c_name,
                    "Currency Unichar": c_symbol,
                    "Code": analysis_code,
                    "Unit": scale["unit"],
                    "Dividend": scale["dividend"],
                    "Short Form": scale["short"],
                    "Long Form": scale["long"],
                    "Long Text": scale["text"],
                    "UOM": c_symbol if scale["type"] == "Amount" else "Units",
                    "SNAPSHOT_DT": snapshot
                })
                analysis_code += 1

        return rows

