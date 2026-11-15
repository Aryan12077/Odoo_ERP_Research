"""
Geo Master Extractor
Target Table: "EVA_BI"."GEO_MASTER"
Target Temp Table: "EVA_BI"."GEO_MASTER_TEMP"
Source Models: "stock.warehouse", "stock.location", "res.company"

Columns:
- GROUP_COMPANY_CODE (varchar)
- COMPANY_CODE (varchar)
- BRANCH_ID (varchar)
- BRANCH_NAME (varchar)
- BRANCH_CITY (varchar)
- BRANCH_COUNTRY (varchar)
- BRANCH_TYPE (varchar)
- BRANCH_SIZE (varchar)
- BRANCH_AREA_IN_SQM (numeric)
- STORE_ID (varchar)
- STORE_NAME (varchar)
- STORE_LOCATION (varchar)
- STORE_TYPE (varchar)
- STORE_AREA_IN_SQM (numeric)
- STORE_CAPACITY_IN_K_LT (numeric)
- WAREHOUSE_NAME (varchar)
- WAREHOUSE_ID (varchar)
- WAREHOUSE_TYPE (varchar)
- WAREHOUSE_LOCATION (varchar)
- WAREHOUSE_CAPACITY_IN_K_LT (numeric)
- WAREHOUSE_GROUP (varchar)
- SNAPSHOT_DT (timestamp)
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


class GeoMasterExtractor(BaseExtractor):
    """
    Extracts geographical and facility hierarchy: Company -> Warehouse -> Storage Locations / Stores.
    """
    target_table = "GEO_MASTER"
    procedure_name = "sp_update_geo_master"

    def __init__(self, domain: Optional[list] = None):
        self.custom_domain = domain

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        # 1. Fetch Companies
        companies = client.search_read(
            model="res.company",
            domain=[],
            fields=["id", "name", "partner_id"]
        )
        comp_map = {c["id"]: c for c in companies}

        # 2. Fetch Warehouses
        warehouses = client.search_read(
            model="stock.warehouse",
            domain=[],
            fields=["id", "name", "code", "company_id", "partner_id"]
        )
        wh_map = {w["id"]: w for w in warehouses}

        # 3. Fetch Internal / Transit Storage Locations
        loc_domain = [
            ("usage", "in", ["internal", "transit"]),
        ]
        if self.custom_domain:
            loc_domain.extend(self.custom_domain)

        locations = client.search_read(
            model="stock.location",
            domain=loc_domain,
            fields=["id", "name", "complete_name", "usage", "warehouse_id", "company_id", "location_id"],
            order="id asc"
        )

        rows = []
        snapshot = datetime.now()

        # If locations are returned, map each location to its warehouse
        if locations:
            for loc in locations:
                comp_id = get_m2o_id(loc.get("company_id")) or 1
                comp_info = comp_map.get(comp_id, {})
                comp_code = pad_code(comp_id)
                comp_name = comp_info.get("name", "Roshni Distributors Ltd")

                wh_id = get_m2o_id(loc.get("warehouse_id"))
                wh_info = wh_map.get(wh_id, {}) if wh_id else {}

                wh_name = wh_info.get("name") or get_m2o_name(loc.get("warehouse_id"), "MAIN WAREHOUSE")
                wh_code = wh_info.get("code") or (wh_name[:5].upper() if wh_name else "MAIN")

                rows.append({
                    "GROUP_COMPANY_CODE": comp_code,
                    "COMPANY_CODE": comp_code,
                    "BRANCH_ID": comp_code,
                    "BRANCH_NAME": comp_name,
                    "BRANCH_CITY": "Nairobi",
                    "BRANCH_COUNTRY": "Kenya",
                    "BRANCH_TYPE": "Main Branch",
                    "BRANCH_SIZE": "Standard",
                    "BRANCH_AREA_IN_SQM": 0.0,
                    "STORE_ID": str(loc["id"]),
                    "STORE_NAME": loc.get("name") or "Store",
                    "STORE_LOCATION": loc.get("complete_name") or loc.get("name") or "Store",
                    "STORE_TYPE": loc.get("usage") or "internal",
                    "STORE_AREA_IN_SQM": 0.0,
                    "STORE_CAPACITY_IN_K_LT": 0.0,
                    "WAREHOUSE_NAME": wh_name,
                    "WAREHOUSE_ID": wh_code,
                    "WAREHOUSE_TYPE": "Physical",
                    "WAREHOUSE_LOCATION": wh_name,
                    "WAREHOUSE_CAPACITY_IN_K_LT": 0.0,
                    "WAREHOUSE_GROUP": "General",
                    "SNAPSHOT_DT": snapshot
                })

        # Fallback if no locations: emit rows directly for each warehouse
        elif warehouses:
            for w in warehouses:
                comp_id = get_m2o_id(w.get("company_id")) or 1
                comp_info = comp_map.get(comp_id, {})
                comp_code = pad_code(comp_id)
                comp_name = comp_info.get("name", "Roshni Distributors Ltd")

                rows.append({
                    "GROUP_COMPANY_CODE": comp_code,
                    "COMPANY_CODE": comp_code,
                    "BRANCH_ID": comp_code,
                    "BRANCH_NAME": comp_name,
                    "BRANCH_CITY": "Nairobi",
                    "BRANCH_COUNTRY": "Kenya",
                    "BRANCH_TYPE": "Main Branch",
                    "BRANCH_SIZE": "Standard",
                    "BRANCH_AREA_IN_SQM": 0.0,
                    "STORE_ID": str(w["id"]),
                    "STORE_NAME": w.get("name") or "Main Store",
                    "STORE_LOCATION": w.get("name") or "Main Store",
                    "STORE_TYPE": "internal",
                    "STORE_AREA_IN_SQM": 0.0,
                    "STORE_CAPACITY_IN_K_LT": 0.0,
                    "WAREHOUSE_NAME": w.get("name") or "MAIN WAREHOUSE",
                    "WAREHOUSE_ID": w.get("code") or "MAIN",
                    "WAREHOUSE_TYPE": "Physical",
                    "WAREHOUSE_LOCATION": w.get("name") or "MAIN WAREHOUSE",
                    "WAREHOUSE_CAPACITY_IN_K_LT": 0.0,
                    "WAREHOUSE_GROUP": "General",
                    "SNAPSHOT_DT": snapshot
                })

        return rows

