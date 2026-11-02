"""
Branch Master Extractor
Target Table: "EVA_BI"."BRANCH_MASTER"
Target Temp Table: "EVA_BI"."BRANCH_MASTER_TEMP"
Source Model: "res.company" (and/or stock.warehouse)
"""

from datetime import datetime
from typing import Any
from connector import OdooClient
from pipelines.base import (
    BaseExtractor,
    get_m2o_id,
    pad_code,
)


class BranchMasterExtractor(BaseExtractor):
    """
    Extracts branches/operating units from Odoo company/warehouse structure.
    """
    target_table = "BRANCH_MASTER"
    procedure_name = "sp_update_branch_master"

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        companies = client.search_read(
            model="res.company",
            fields=["id", "name", "parent_id"]
        )

        rows = []
        snapshot = datetime.now()

        for c in companies:
            parent_id = get_m2o_id(c.get("parent_id"))
            group_code = pad_code(parent_id if parent_id else c["id"])
            comp_code = pad_code(c["id"])

            rows.append({
                "GROUP_COMPANY_CODE": group_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "BRANCH": c.get("name") or "Main Branch",
                "LOCATION_TYPE": "Branch",
                "LOCATION_CATEGORY": "Head Office",
                "SNAPSHOT_DT": snapshot
            })

        return rows

