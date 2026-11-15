"""
Product Master Extractor
Target Table: "EVA_BI"."PRODUCT_MASTER"
Target Temp Table: "EVA_BI"."PRODUCT_MASTER_TEMP"
Source Model: "product.template"

Columns:
- 63 Columns as defined in Table_references.sql
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


class ProductMasterExtractor(BaseExtractor):
    """
    Extracts products, multi-level category hierarchy, pricing, and UOM from Odoo product.template.
    """
    target_table = "PRODUCT_MASTER"
    procedure_name = "sp_update_product_master"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 5000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("active", "=", True),
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "default_code",
            "name",
            "list_price",
            "standard_price",
            "uom_id",
            "categ_id",
            "company_id",
            "create_date",
            "weight",
            "qty_available",
            "seller_ids",
        ]

        products = client.search_read(
            model="product.template",
            domain=base_domain,
            fields=fields,
            limit=self.batch_limit,
            order="id asc"
        )

        if not products:
            return []

        # Load product category hierarchy mapping (id -> complete_name)
        cat_map = {}
        try:
            cats = client.search_read("product.category", fields=["id", "complete_name"])
            for c in cats:
                cat_map[c["id"]] = c.get("complete_name") or ""
        except Exception:
            pass

        # Resolve primary supplier information for products
        seller_ids = set()
        for pt in products:
            sids = pt.get("seller_ids")
            if sids:
                seller_ids.add(sids[0])

        seller_map = {}
        if seller_ids:
            seller_list = list(seller_ids)
            for i in range(0, len(seller_list), 500):
                chunk = seller_list[i:i + 500]
                try:
                    sinfos = client.search_read(
                        model="product.supplierinfo",
                        domain=[("id", "in", chunk)],
                        fields=["id", "partner_id", "delay"]
                    )
                    for s in sinfos:
                        seller_map[s["id"]] = s
                except Exception:
                    pass

        rows = []
        snapshot = datetime.now()

        for pt in products:
            comp_id = get_m2o_id(pt.get("company_id")) or 1
            comp_code = pad_code(comp_id)

            prod_code = pt.get("default_code") or str(pt["id"])
            prod_name = (pt.get("name") or "NA").strip()

            uom_name = get_m2o_name(pt.get("uom_id"), "Unit")
            categ_id = get_m2o_id(pt.get("categ_id"))
            
            # Resolve category levels
            cat_path = cat_map.get(categ_id, get_m2o_name(pt.get("categ_id"), "General"))
            cat_parts = [p.strip() for p in cat_path.split("/") if p.strip()]
            group_name = cat_parts[0] if len(cat_parts) > 0 else "General"
            sub_group = cat_parts[1] if len(cat_parts) > 1 else "NA"
            sub_sub_group = cat_parts[2] if len(cat_parts) > 2 else "NA"

            sale_price = safe_num(pt.get("list_price"))
            cost_price = safe_num(pt.get("standard_price"))
            creation_date = parse_date(pt.get("create_date"))
            weight = safe_num(pt.get("weight"))
            stock_qty = safe_num(pt.get("qty_available"))

            # Supplier resolution
            first_seller_id = (pt.get("seller_ids") or [None])[0]
            sup_info = seller_map.get(first_seller_id, {})
            supplier_name = get_m2o_name(sup_info.get("partner_id"), "NA")
            lead_time = safe_num(sup_info.get("delay"), 1.0)
            if lead_time <= 0:
                lead_time = 1.0

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "PRODUCT_CODE": prod_code,
                "AEDESC": prod_name,
                "MAKE": "NA",
                "OEM": "NA",
                "APP": "NA",
                "PARTNO2": "NA",
                "SIZE": "NA",
                "PRODUCT": prod_name,
                "UNIT_CODE": uom_name,
                "UNIT": uom_name,
                "WEIGHT_UNIT": "KGS",
                "KGS_FOR_PCS": weight,
                "WEIGHT_PCS": weight,
                "GROUP_CODE": str(categ_id) if categ_id else "NA",
                "GROUP_NAME": group_name,
                "CLASSIFICATION_CODE": "NA",
                "CLASSIFICATION": group_name,
                "SUB_GROUP_CODE": "NA",
                "SUB_GROUP": sub_group,
                "SUB_SUB_GROUP_CODE": "NA",
                "SUB_SUB_GROUP": sub_sub_group,
                "CREATION_DATE": creation_date,
                "BRAND_CODE": "NA",
                "BRAND": "NA",
                "FIRST_SALE_DATE": None,
                "LAST_SALE_DATE": None,
                "FIRST_PURCHASE_QUANTITY": 0.0,
                "LAST_PURCHASE_QUANTITY": 0.0,
                "FIRST_SALE_QUANTITY": 0.0,
                "LAST_SALE_QUANTITY": 0.0,
                "RID": 0.0,
                "PRODUCT_PRICE": cost_price,
                "PRODUCT_PRICE_USD": cost_price,
                "SALE_PRICE": sale_price,
                "SALE_PRICE_USD": sale_price,
                "SBU_CODE": "NA",
                "SBU": "NA",
                "STOCK_QUANTITY": stock_qty,
                "REORDER_LEVEL": 0.0,
                "LEAD_TIME_IN_DAYS": lead_time,
                "WARRANTY_IN_MONTHS": 0.0,
                "SUPPLIER": supplier_name,
                "DISCOUNT_PERCENTAGE": 0.0,
                "TAX_RATE": 0.0,
                "SHIPPING_COST": 0.0,
                "STORAGE_LOCATION": "MAIN STORE",
                "MIN_LEVEL": 0.0,
                "MAX_LEVEL": 0.0,
                "PO_PROCESS_DAYS": 0.0,
                "LOGISTICS_DAYS": 0.0,
                "SAFETY_STOCK": 0.0,
                "FIRST_PURCHASE_DATE": None,
                "LAST_PURCHASE_DATE": None,
                "ABC": "NA",
                "VED": "NA",
                "PRINCIPAL_CODE": "NA",
                "PRINCIPAL": "NA",
                "STYLE": "NA",
                "CARTON_QUANTITY": 1.0,
                "SNAPSHOT_DT": snapshot
            })

        return rows
