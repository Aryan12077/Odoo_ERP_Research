"""
Inventory Ageing Extractor
Target Table: "EVA_BI"."INVENTORY_AGEING"
Target Temp Table: "EVA_BI"."INVENTORY_AGEING_TEMP"
Source Model: "stock.quant" (joined with "product.product" for standard costs)

Columns:
- GROUP_COMPANY_CODE (varchar)
- COMPANY_CODE (varchar)
- BRANCH_ID (varchar)
- WAREHOUSE_ID (varchar)
- PRODUCT_CODE (varchar)
- BIN_NO (numeric)
- CONSIGN_NO (numeric)
- PURCHASE_DATE (timestamp)
- INVENTORY_DATE (timestamp)
- PURCHASE_QUANTITY (numeric)
- TOTAL_CONSUMPTION (numeric)
- REMAINING_QUANTITY (numeric)
- REMAINING_VALUE_USD (numeric)
- REMAINING_VALUE_AUD (numeric)
- PURCHASE_VALUE_USD (numeric)
- PURCHASE_VALUE_AUD (numeric)
- ITEM_UNIT_COST_USD (numeric)
- ITEM_UNIT_COST_AUD (numeric)
- RETURN_QUANTITY (numeric)
- SALE_QUANTITY (numeric)
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
    safe_num,
    parse_date,
)


class InventoryAgeingExtractor(BaseExtractor):
    """
    Extracts current on-hand stock and valuations per location and product.
    Enriched with Warehouse identification from stock.quant.
    """
    target_table = "INVENTORY_AGEING"
    procedure_name = "sp_update_inventory_ageing"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 5000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        # 1. Fetch positive stock quants in internal locations
        quant_domain = [
            ("location_id.usage", "=", "internal"),
            ("quantity", ">", 0),
        ]
        if self.custom_domain:
            quant_domain.extend(self.custom_domain)

        quant_fields = [
            "id",
            "product_id",
            "location_id",
            "warehouse_id",
            "company_id",
            "quantity",
            "in_date"
        ]

        quants = client.search_read(
            model="stock.quant",
            domain=quant_domain,
            fields=quant_fields,
            limit=self.batch_limit,
            order="in_date desc"
        )

        if not quants:
            return []

        # 2. Extract product IDs to fetch standard unit costs in bulk
        product_ids = list({get_m2o_id(q.get("product_id")) for q in quants if get_m2o_id(q.get("product_id"))})
        costs_map = {}
        if product_ids:
            for i in range(0, len(product_ids), 500):
                chunk = product_ids[i:i + 500]
                prods = client.search_read(
                    model="product.product",
                    domain=[("id", "in", chunk)],
                    fields=["id", "default_code", "standard_price"]
                )
                for p in prods:
                    costs_map[p["id"]] = {
                        "code": p.get("default_code") or str(p["id"]),
                        "cost": safe_num(p.get("standard_price"))
                    }

        rows = []
        snapshot = datetime.now()

        for q in quants:
            comp_id = get_m2o_id(q.get("company_id")) or 1
            comp_code = pad_code(comp_id)

            p_id = get_m2o_id(q.get("product_id"))
            prod_info = costs_map.get(p_id, {"code": str(p_id), "cost": 0.0})
            prod_code = prod_info["code"]
            unit_cost = prod_info["cost"]

            qty = safe_num(q.get("quantity"))
            val = round(qty * unit_cost, 2)
            in_date = parse_date(q.get("in_date"))

            # Clean Warehouse extraction
            wh_name = get_m2o_name(q.get("warehouse_id"))
            if not wh_name or wh_name == "NA":
                wh_name = get_m2o_name(q.get("location_id"), "MAIN WAREHOUSE")

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "WAREHOUSE_ID": wh_name,
                "PRODUCT_CODE": prod_code,
                "BIN_NO": 0,
                "CONSIGN_NO": 0,
                "PURCHASE_DATE": in_date,
                "INVENTORY_DATE": snapshot.strftime("%Y-%m-%d %H:%M:%S"),
                "PURCHASE_QUANTITY": qty,
                "TOTAL_CONSUMPTION": 0.0,
                "REMAINING_QUANTITY": qty,
                "REMAINING_VALUE_USD": val,
                "REMAINING_VALUE_AUD": val,
                "PURCHASE_VALUE_USD": val,
                "PURCHASE_VALUE_AUD": val,
                "ITEM_UNIT_COST_USD": unit_cost,
                "ITEM_UNIT_COST_AUD": unit_cost,
                "RETURN_QUANTITY": 0.0,
                "SALE_QUANTITY": 0.0,
                "SNAPSHOT_DT": snapshot
            })

        return rows
