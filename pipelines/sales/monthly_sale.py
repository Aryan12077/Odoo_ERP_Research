"""
Monthly Sale Aggregator
Target Table: "EVA_BI"."MONTHLY_SALE"
Target Temp Table: "EVA_BI"."MONTHLY_SALE_TEMP"
Source Model: "account.move" (posted customer invoices aggregated by month & customer)

Columns:
- GROUP_COMPANY_CODE (varchar)
- COMPANY_CODE (varchar)
- BRANCH_ID (varchar)
- ACCOUNT_CODE (integer)
- FOR_MONTH (timestamp)
- SALE_VALUE_USD (numeric)
- INVOICE_DATE (timestamp)
- SALE_VALUE_AUD (numeric)
- INVOICE_VALUE (numeric)
- REGION (varchar)
- SNAPSHOT_DT (timestamp)
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Optional
from connector import OdooClient
from pipelines.base import (
    BaseExtractor,
    get_m2o_id,
    pad_code,
    safe_num,
    parse_date,
)


class MonthlySaleExtractor(BaseExtractor):
    """
    Extracts and aggregates monthly sales figures per customer and company.
    """
    target_table = "MONTHLY_SALE"
    procedure_name = "sp_update_monthly_sale"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 10000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("state", "=", "posted"),
            ("move_type", "in", ["out_invoice", "out_refund"]),
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "invoice_date",
            "partner_id",
            "company_id",
            "amount_total",
            "amount_untaxed",
            "move_type"
        ]

        moves = client.search_read(
            model="account.move",
            domain=base_domain,
            fields=fields,
            limit=self.batch_limit,
            order="invoice_date desc"
        )

        # Aggregate by (company_id, partner_id, year_month)
        grouped = defaultdict(lambda: {
            "invoice_value": 0.0,
            "sale_value": 0.0,
            "latest_invoice_date": None
        })

        for m in moves:
            dt_str = m.get("invoice_date")
            if not dt_str:
                continue

            # Year-Month date: YYYY-MM-01
            for_month = f"{dt_str[:7]}-01 00:00:00"
            comp_id = get_m2o_id(m.get("company_id")) or 1
            partner_id = get_m2o_id(m.get("partner_id")) or 0

            sign = -1.0 if m.get("move_type") == "out_refund" else 1.0
            amount_total = safe_num(m.get("amount_total")) * sign
            amount_untaxed = safe_num(m.get("amount_untaxed")) * sign

            key = (comp_id, partner_id, for_month)
            grouped[key]["invoice_value"] += amount_total
            grouped[key]["sale_value"] += amount_untaxed

            if (not grouped[key]["latest_invoice_date"] or 
                dt_str > grouped[key]["latest_invoice_date"]):
                grouped[key]["latest_invoice_date"] = dt_str

        rows = []
        snapshot = datetime.now()

        for (comp_id, partner_id, for_month), data in grouped.items():
            code = pad_code(comp_id)
            rows.append({
                "GROUP_COMPANY_CODE": code,
                "COMPANY_CODE": code,
                "BRANCH_ID": code,
                "ACCOUNT_CODE": partner_id,
                "FOR_MONTH": for_month,
                "SALE_VALUE_USD": round(data["sale_value"], 2),
                "INVOICE_DATE": parse_date(data["latest_invoice_date"]),
                "SALE_VALUE_AUD": round(data["sale_value"], 2),
                "INVOICE_VALUE": round(data["invoice_value"], 2),
                "REGION": "NA",
                "SNAPSHOT_DT": snapshot
            })

        return rows

