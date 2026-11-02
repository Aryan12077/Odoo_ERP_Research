"""
Supplier Master Extractor
Target Table: "EVA_BI"."SUPPLIER_MASTER"
Target Temp Table: "EVA_BI"."SUPPLIER_MASTER_TEMP"
Source Model: "res.partner" (where supplier_rank > 0)
"""

from datetime import datetime
from typing import Any, Optional
from connector import OdooClient
from pipelines.base import (
    BaseExtractor,
    get_m2o_id,
    get_m2o_name,
    pad_code,
)


class SupplierMasterExtractor(BaseExtractor):
    """
    Extracts Vendor profiles and contact mappings from Odoo res.partner.
    """
    target_table = "SUPPLIER_MASTER"
    procedure_name = "sp_update_supplier_master"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 5000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("supplier_rank", ">", 0),
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "name",
            "city",
            "state_id",
            "country_id",
            "phone",
            "company_id"
        ]

        partners = client.search_read(
            model="res.partner",
            domain=base_domain,
            fields=fields,
            limit=self.batch_limit,
            order="id asc"
        )

        rows = []
        snapshot = datetime.now()

        for p in partners:
            comp_id = get_m2o_id(p.get("company_id")) or 1
            comp_code = pad_code(comp_id)

            country_id = get_m2o_id(p.get("country_id"))
            country_name = get_m2o_name(p.get("country_id"), "KENYA")

            state_id = get_m2o_id(p.get("state_id"))
            state_name = get_m2o_name(p.get("state_id"), "NA")

            city_name = p.get("city") or "NA"

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "SUPPLIER_CODE": p["id"],
                "SUPPLIER": p.get("name") or "NA",
                "CATEGORY_CODE": "NA",
                "CATEGORY": "General",
                "STATE_CODE": str(state_id) if state_id else "NA",
                "STATE": state_name,
                "CITY_CODE": "NA",
                "CITY": city_name,
                "COUNTRY_CODE": str(country_id) if country_id else "254",
                "COUNTRY": country_name,
                "ACCOUNT_CODE": p["id"],
                "RID": 0.0,
                "SNAPSHOT_DT": snapshot
            })

        return rows

