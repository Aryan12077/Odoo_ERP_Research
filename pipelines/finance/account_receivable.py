"""
Account Receivable (Open AR Subledger) Extractor
Target Table: "EVA_BI"."ACCOUNT_RECEIVABLE"
Target Temp Table: "EVA_BI"."ACCOUNT_RECEIVABLE_TEMP"
Source Model: "account.move.line" (posted receivable lines with residual != 0)
"""

from datetime import datetime, date
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


class AccountReceivableExtractor(BaseExtractor):
    """
    Extracts open accounts receivable balances and aging buckets.
    """
    target_table = "ACCOUNT_RECEIVABLE"
    procedure_name = "sp_update_account_receivable"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 5000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("parent_state", "=", "posted"),
            ("account_id.account_type", "=", "asset_receivable"),
            ("amount_residual", "!=", 0),
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "move_id",
            "date",
            "partner_id",
            "account_id",
            "debit",
            "credit",
            "amount_residual",
            "date_maturity",
            "company_id"
        ]

        lines = client.search_read(
            model="account.move.line",
            domain=base_domain,
            fields=fields,
            limit=self.batch_limit,
            order="date desc, id desc"
        )

        rows = []
        today = date.today()
        snapshot = datetime.now()

        for line in lines:
            comp_id = get_m2o_id(line.get("company_id")) or 1
            comp_code = pad_code(comp_id)

            account_id = get_m2o_id(line.get("account_id"))
            partner_id = get_m2o_id(line.get("partner_id")) or 0

            move_display = get_m2o_name(line.get("move_id"), "")
            invoice_num = move_display.split()[0] if move_display else "NA"

            inv_date_str = line.get("date")
            inv_date = parse_date(inv_date_str)
            due_date = parse_date(line.get("date_maturity")) or inv_date

            debit = safe_num(line.get("debit"))
            credit = safe_num(line.get("credit"))
            invoice_amount = debit if debit > 0 else (debit - credit)
            outstanding = safe_num(line.get("amount_residual"))
            amount_paid = invoice_amount - outstanding

            # Calculate aging days
            aging_days = 0
            if inv_date_str:
                try:
                    dt = datetime.strptime(inv_date_str[:10], "%Y-%m-%d").date()
                    aging_days = max(0, (today - dt).days)
                except Exception:
                    aging_days = 0

            # Durations (aging buckets)
            d1 = outstanding if aging_days <= 30 else 0.0
            d2 = outstanding if 31 <= aging_days <= 60 else 0.0
            d3 = outstanding if 61 <= aging_days <= 90 else 0.0
            d4 = outstanding if 91 <= aging_days <= 120 else 0.0
            d5 = outstanding if aging_days > 120 else 0.0

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "VOUCHER_NUMBER": invoice_num,
                "VOUCHER_DATE": inv_date,
                "ACCOUNT_CODE": account_id,
                "INVOICE_NUMBER": invoice_num,
                "INVOICE_DATE": inv_date,
                "DUE_DATE": due_date,
                "OUTSTANDING_DATE": snapshot.strftime("%Y-%m-%d %H:%M:%S"),
                "INVOICE_AMOUNT": invoice_amount,
                "OUTSTANDING": outstanding,
                "CURRENCY_CODE": 1,
                "AMOUNT_PAID": amount_paid,
                "OUTSTANDING_DAYS": aging_days,
                "REGION": "NA",
                "INVOICE_AMOUNT_BASE": invoice_amount,
                "INVOICE_AMOUNT_REPORTING": invoice_amount,
                "OUTSTANDING_BASE": outstanding,
                "OUTSTANDING_REPORTING": outstanding,
                "AMOUNT_PAID_BASE": amount_paid,
                "AMOUNT_PAID_REPORTING": amount_paid,
                "CUSTOMER_CATEGORY": "NA",
                "DURATION1": d1,
                "DURATION2": d2,
                "DURATION3": d3,
                "DURATION4": d4,
                "DURATION5": d5,
                "DURATION1_BASE": d1,
                "DURATION2_BASE": d2,
                "DURATION3_BASE": d3,
                "DURATION4_BASE": d4,
                "DURATION5_BASE": d5,
                "SNAPSHOT_DT": snapshot
            })

        return rows

