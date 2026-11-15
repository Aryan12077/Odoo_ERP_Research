"""
Sales Data Extractor
Target Table: "EVA_BI"."SALES_DATA"
Target Temp Table: "EVA_BI"."SALES_DATA_TEMP"
Source Model: "account.move.line" (linked to posted "out_invoice" / "out_refund")

Columns:
- GROUP_COMPANY_CODE (varchar)
- COMPANY_CODE (varchar)
- BRANCH_ID (varchar)
- STORE_ID (varchar)
- WAREHOUSE_ID (varchar)
- CUSTOMER_CODE (integer)
- INVOICE_DATE (timestamp)
- INVOICE_NUMBER (varchar)
- PRODUCT_CODE (varchar)
- EXECUTIVE_ID (varchar)
- EXECUTIVE (varchar)
- INVOICE_CURRENCY (numeric)
- EXCHANGE_RATE (numeric)
- SALE_QUANTITY (numeric)
- SALE_VALUE_USD (numeric)
- SALE_VALUE_AUD (numeric)
- COGS_USD (numeric)
- COGS_AUD (numeric)
- SALE_TYPE (varchar)
- SALE_WO_TAX_USD (numeric)
- SALE_WO_TAX_AUD (numeric)
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


class SalesDataExtractor(BaseExtractor):
    """
    Extracts sales line item transactions from posted customer invoices/refunds.
    Enriched with Warehouse, Salesperson, and COGS calculations.
    """
    target_table = "SALES_DATA"
    procedure_name = "sp_update_sales_data"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 5000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        # 1. Fetch posted customer invoice and credit note lines
        base_domain = [
            ("parent_state", "=", "posted"),
            ("move_type", "in", ["out_invoice", "out_refund"]),
            ("display_type", "in", ["product", False]),
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "move_id",
            "move_name",
            "date",
            "partner_id",
            "product_id",
            "quantity",
            "price_unit",
            "price_subtotal",
            "price_total",
            "company_id",
            "currency_id",
            "currency_rate",
            "move_type"
        ]

        lines = client.search_read(
            model="account.move.line",
            domain=base_domain,
            fields=fields,
            limit=self.batch_limit,
            order="date desc, id desc"
        )

        if not lines:
            return []

        # 2. Batch lookup parent invoices to retrieve Salesperson
        move_ids = list({get_m2o_id(l.get("move_id")) for l in lines if get_m2o_id(l.get("move_id"))})
        move_map = {}
        if move_ids:
            for i in range(0, len(move_ids), 500):
                chunk = move_ids[i:i + 500]
                try:
                    moves = client.search_read(
                        model="account.move",
                        domain=[("id", "in", chunk)],
                        fields=["id", "name", "invoice_user_id"]
                    )
                    for m in moves:
                        move_map[m["id"]] = m
                except Exception:
                    pass

        # 3. Batch lookup product standard costs for COGS calculation
        product_ids = list({get_m2o_id(l.get("product_id")) for l in lines if get_m2o_id(l.get("product_id"))})
        costs_map = {}
        if product_ids:
            for i in range(0, len(product_ids), 500):
                chunk = product_ids[i:i + 500]
                try:
                    prods = client.search_read(
                        model="product.product",
                        domain=[("id", "in", chunk)],
                        fields=["id", "standard_price"]
                    )
                    for p in prods:
                        costs_map[p["id"]] = safe_num(p.get("standard_price"))
                except Exception:
                    pass

        rows = []
        snapshot = datetime.now()

        for line in lines:
            move_type = line.get("move_type")
            is_refund = (move_type == "out_refund")
            sign = -1.0 if is_refund else 1.0

            company_id = get_m2o_id(line.get("company_id")) or 1
            company_code = pad_code(company_id)

            partner_id = get_m2o_id(line.get("partner_id"))
            product_id = get_m2o_id(line.get("product_id"))
            product_name = get_m2o_name(line.get("product_id"), "")

            # If product code is bracketed e.g. [H1041], extract code; fallback to ID
            product_code = str(product_id) if product_id else "NA"
            if product_name and product_name.startswith("[") and "]" in product_name:
                product_code = product_name[1:product_name.find("]")]

            # Clean invoice number
            parent_move_id = get_m2o_id(line.get("move_id"))
            move_info = move_map.get(parent_move_id, {})
            invoice_num = line.get("move_name") or move_info.get("name") or get_m2o_name(line.get("move_id"), "NA")

            # Salesperson mapping: move invoice_user_id
            exec_id = get_m2o_id(move_info.get("invoice_user_id"))
            exec_name = get_m2o_name(move_info.get("invoice_user_id"), "NA")

            # Warehouse resolution (Roshni primary distribution hub)
            wh_name = "MAIN WAREHOUSE"
            wh_code = "RDL"

            qty = safe_num(line.get("quantity")) * sign
            subtotal = safe_num(line.get("price_subtotal")) * sign
            total = safe_num(line.get("price_total")) * sign
            currency_id = get_m2o_id(line.get("currency_id")) or 1
            currency_rate = safe_num(line.get("currency_rate"), 1.0)

            # COGS calculation: quantity * standard_price
            unit_cost = costs_map.get(product_id, 0.0)
            cogs_val = round(abs(qty) * unit_cost, 2)

            rows.append({
                "GROUP_COMPANY_CODE": company_code,
                "COMPANY_CODE": company_code,
                "BRANCH_ID": company_code,
                "STORE_ID": wh_code,
                "WAREHOUSE_ID": wh_name,
                "CUSTOMER_CODE": partner_id,
                "INVOICE_DATE": parse_date(line.get("date")),
                "INVOICE_NUMBER": invoice_num,
                "PRODUCT_CODE": product_code,
                "EXECUTIVE_ID": str(exec_id) if exec_id else "NA",
                "EXECUTIVE": exec_name,
                "INVOICE_CURRENCY": currency_id,
                "EXCHANGE_RATE": currency_rate,
                "SALE_QUANTITY": qty,
                "SALE_VALUE_USD": total,
                "SALE_VALUE_AUD": total,
                "COGS_USD": cogs_val,
                "COGS_AUD": cogs_val,
                "SALE_TYPE": "Credit" if not is_refund else "Refund",
                "SALE_WO_TAX_USD": subtotal,
                "SALE_WO_TAX_AUD": subtotal,
                "SNAPSHOT_DT": snapshot
            })

        return rows
