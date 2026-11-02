"""
Customer Master Extractor
Target Table: "EVA_BI"."CUSTOMER_MASTER"
Target Temp Table: "EVA_BI"."CUSTOMER_MASTER_TEMP"
Source Model: "res.partner" (where customer_rank > 0)
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


class CustomerMasterExtractor(BaseExtractor):
    """
    Extracts Customer profiles and geographical/contact mappings from Odoo res.partner.
    Enriched with Industry information from res.partner.
    """
    target_table = "CUSTOMER_MASTER"
    procedure_name = "sp_update_customer_master"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 5000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("customer_rank", ">", 0),
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "name",
            "user_id",
            "industry_id",
            "city",
            "state_id",
            "country_id",
            "phone",
            "mobile",
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

            exec_id = get_m2o_id(p.get("user_id"))
            exec_name = get_m2o_name(p.get("user_id"), "NA")

            ind_id = get_m2o_id(p.get("industry_id"))
            ind_name = get_m2o_name(p.get("industry_id"), "NA")

            country_id = get_m2o_id(p.get("country_id"))
            country_name = get_m2o_name(p.get("country_id"), "KENYA")

            state_id = get_m2o_id(p.get("state_id"))
            state_name = get_m2o_name(p.get("state_id"), "NA")

            city_name = p.get("city") or "NA"
            phone = p.get("phone") or p.get("mobile") or "NA"

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "CUSTOMER_CODE": p["id"],
                "CUSTOMER_NAME": p.get("name") or "NA",
                "EXECUTIVE_ID": str(exec_id) if exec_id else "NA",
                "EXECUTIVE": exec_name,
                "CATEGORY_CODE": "NA",
                "CATEGORY": "General",
                "ZONE_CODE": "NA",
                "AREA": city_name,
                "STATE_CODE": str(state_id) if state_id else "NA",
                "STATE": state_name,
                "CITY_CODE": "NA",
                "CITY": city_name,
                "COUNTRY_CODE": str(country_id) if country_id else "254",
                "COUNTRY": country_name,
                "INDUSTRY_ID": str(ind_id) if ind_id else "NA",
                "INDUSTRY": ind_name,
                "TYPE_ID": "NA",
                "CUST_TYPE": "Customer",
                "ACCOUNT_CODE": p["id"],
                "RID": 0.0,
                "CREDIT_DAYS": 30.0,
                "CREDIT_LIMIT": 0.0,
                "BILL_AREA": city_name,
                "BILL_REGION": "NA",
                "AVERAGE_BILLING": 0.0,
                "AVERAGE_PAYMENT": 0.0,
                "CURRENCY_CODE": 1,
                "MASTER_ACCOUNT": p["id"],
                "MASTER_ACCOUNT_NAME": p.get("name") or "NA",
                "TELEPHONE": phone,
                "SNAPSHOT_DT": snapshot
            })

        return rows
