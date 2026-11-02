"""
Purchase Data Extractor
Target Table: "EVA_BI"."PURCHASE_DATA"
Target Temp Table: "EVA_BI"."PURCHASE_DATA_TEMP"
Source Model: "purchase.order.line" (linked to purchase.order)

Columns:
- GROUP_COMPANY_CODE (varchar)
- COMPANY_CODE (varchar)
- SUPPLIER_CODE (integer)
- PURCHASE_ORDER_NUMBER (varchar)
- PURCHASE_DATE (timestamp)
- PO_DELIVERY_DATE (varchar)
- ITEM_CODE (varchar)
- ORDERED_QUANTITY (numeric)
- UNIT_PRICE (numeric)
- GRN_NUMBER (varchar)
- GRN_DATE (timestamp)
- BILL_NUMBER (varchar)
- CHALLAN_NUMBER (varchar)
- CHALLAN_DATE (varchar)
- GATE_ENTRY_NUMBER (varchar)
- CHALLAN_QUANTITY (numeric)
- RECEIVED_QUANTITY (numeric)
- ACCEPTED_QUANTITY (numeric)
- PURCHASE_VALUE (numeric)
- PURCHASE_VALUE_BASE (numeric)
- REJECTED_QUANTITY (numeric)
- ACCOUNT_CODE (integer)
- REJECTION_REASON (varchar)
- GATE_ORDER_NUMBER (varchar)
- ORDER_STATUS (varchar)
- EXPECTED_DELIVERY_DATE (timestamp)
- LEAD_TIME (numeric)
- WAREHOUSE_ID (varchar)
- ROW_ID (varchar)
- BRANCH_ID (varchar)
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


class PurchaseDataExtractor(BaseExtractor):
    """
    Extracts Purchase Order lines from Odoo purchase.order.line.
    Enriched with Warehouse, GRN Number (stock.picking), and Bill Number (account.move).
    """
    target_table = "PURCHASE_DATA"
    procedure_name = "sp_update_purchase_data"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 5000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("state", "in", ["purchase", "done"]),
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "order_id",
            "partner_id",
            "product_id",
            "product_qty",
            "qty_received",
            "price_unit",
            "price_subtotal",
            "date_planned",
            "company_id",
            "state"
        ]

        lines = client.search_read(
            model="purchase.order.line",
            domain=base_domain,
            fields=fields,
            limit=self.batch_limit,
            order="id desc"
        )

        if not lines:
            return []

        # Batch lookup parent purchase orders for Warehouse, Picking, and Bill linkage
        order_ids = list({get_m2o_id(l.get("order_id")) for l in lines if get_m2o_id(l.get("order_id"))})
        order_map = {}
        all_picking_ids = set()
        all_bill_ids = set()

        if order_ids:
            for i in range(0, len(order_ids), 500):
                chunk = order_ids[i:i + 500]
                orders = client.search_read(
                    model="purchase.order",
                    domain=[("id", "in", chunk)],
                    fields=["id", "name", "picking_type_id", "picking_ids", "invoice_ids"]
                )
                for o in orders:
                    order_map[o["id"]] = o
                    for pid in o.get("picking_ids", []):
                        all_picking_ids.add(pid)
                    for bid in o.get("invoice_ids", []):
                        all_bill_ids.add(bid)

        # Batch lookup first picking (GRN) details
        picking_map = {}
        if all_picking_ids:
            p_list = list(all_picking_ids)[:500]
            pickings = client.search_read(
                model="stock.picking",
                domain=[("id", "in", p_list)],
                fields=["id", "name", "date_done"]
            )
            for p in pickings:
                picking_map[p["id"]] = p

        # Batch lookup first vendor bill details
        bill_map = {}
        if all_bill_ids:
            b_list = list(all_bill_ids)[:500]
            bills = client.search_read(
                model="account.move",
                domain=[("id", "in", b_list)],
                fields=["id", "name"]
            )
            for b in bills:
                bill_map[b["id"]] = b

        rows = []
        snapshot = datetime.now()

        for line in lines:
            comp_id = get_m2o_id(line.get("company_id")) or 1
            comp_code = pad_code(comp_id)

            supplier_id = get_m2o_id(line.get("partner_id"))
            product_id = get_m2o_id(line.get("product_id"))
            product_name = get_m2o_name(line.get("product_id"), "")

            product_code = str(product_id) if product_id else "NA"
            if product_name and product_name.startswith("[") and "]" in product_name:
                product_code = product_name[1:product_name.find("]")]

            order_id = get_m2o_id(line.get("order_id"))
            o_info = order_map.get(order_id, {})
            order_name = o_info.get("name") or get_m2o_name(line.get("order_id"), "")
            po_number = order_name.split()[0] if order_name else "NA"

            # Warehouse derivation
            pt = get_m2o_name(o_info.get("picking_type_id"), "NA")
            wh_name = pt.split(":")[0].strip() if ":" in pt else (pt if pt != "NA" else "MAIN WAREHOUSE")

            # GRN & Bill Number linkage
            grn_num = "NA"
            grn_date = parse_date(line.get("date_planned"))
            p_ids = o_info.get("picking_ids", [])
            if p_ids and p_ids[0] in picking_map:
                grn_info = picking_map[p_ids[0]]
                grn_num = grn_info.get("name") or "NA"
                if grn_info.get("date_done"):
                    grn_date = parse_date(grn_info.get("date_done"))

            bill_num = "NA"
            b_ids = o_info.get("invoice_ids", [])
            if b_ids and b_ids[0] in bill_map:
                bill_num = bill_map[b_ids[0]].get("name") or "NA"

            ordered_qty = safe_num(line.get("product_qty"))
            received_qty = safe_num(line.get("qty_received"))
            unit_price = safe_num(line.get("price_unit"))
            subtotal = safe_num(line.get("price_subtotal"))
            delivery_date = parse_date(line.get("date_planned"))

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "SUPPLIER_CODE": supplier_id,
                "PURCHASE_ORDER_NUMBER": po_number,
                "PURCHASE_DATE": delivery_date,
                "PO_DELIVERY_DATE": str(delivery_date)[:10] if delivery_date else "NA",
                "ITEM_CODE": product_code,
                "ORDERED_QUANTITY": ordered_qty,
                "UNIT_PRICE": unit_price,
                "GRN_NUMBER": grn_num,
                "GRN_DATE": grn_date,
                "BILL_NUMBER": bill_num,
                "CHALLAN_NUMBER": "NA",
                "CHALLAN_DATE": "NA",
                "GATE_ENTRY_NUMBER": "NA",
                "CHALLAN_QUANTITY": ordered_qty,
                "RECEIVED_QUANTITY": received_qty,
                "ACCEPTED_QUANTITY": received_qty,
                "PURCHASE_VALUE": subtotal,
                "PURCHASE_VALUE_BASE": subtotal,
                "REJECTED_QUANTITY": max(0.0, ordered_qty - received_qty),
                "ACCOUNT_CODE": supplier_id,
                "REJECTION_REASON": "NA",
                "GATE_ORDER_NUMBER": "NA",
                "ORDER_STATUS": line.get("state") or "purchase",
                "EXPECTED_DELIVERY_DATE": delivery_date,
                "LEAD_TIME": 0.0,
                "WAREHOUSE_ID": wh_name,
                "ROW_ID": str(line.get("id")),
                "BRANCH_ID": comp_code,
                "SNAPSHOT_DT": snapshot
            })

        return rows
