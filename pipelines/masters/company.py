"""
Company Master Extractor
Target Table: "EVA_BI"."COMPANY_MASTER"
Target Temp Table: "EVA_BI"."COMPANY_MASTER_TEMP"
Source Model: "res.company"
"""

from datetime import datetime
from typing import Any
from connector import OdooClient
from pipelines.base import BaseExtractor, get_m2o_id, get_m2o_name, pad_code


class CompanyMasterExtractor(BaseExtractor):
    """
    Extracts company hierarchy and base currency from Odoo res.company.
    """
    target_table = "COMPANY_MASTER"
    procedure_name = "sp_update_company_master"

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        companies = client.search_read(
            model="res.company",
            fields=[
                "id",
                "name",
                "parent_id",
                "currency_id"
            ]
        )

        rows = []
        snapshot = datetime.now()

        for company in companies:
            parent_id = get_m2o_id(company.get("parent_id"))
            parent_name = get_m2o_name(company.get("parent_id"))
            currency_name = get_m2o_name(company.get("currency_id"))

            group_code = pad_code(parent_id if parent_id else company["id"])
            group_name = parent_name if parent_name else company["name"]
            company_code = pad_code(company["id"])

            rows.append({
                "GROUP_COMPANY_CODE": group_code,
                "GROUP_COMPANY_NAME": group_name,
                "COMPANY_CODE": company_code,
                "COMPANY_NAME": company["name"],
                "BASE_CURRENCY_CODE": currency_name,
                "SNAPSHOT_DT": snapshot
            })

        return rows


def extract(client: OdooClient) -> list[dict[str, Any]]:
    """Functional convenience wrapper."""
    return CompanyMasterExtractor().extract(client)
