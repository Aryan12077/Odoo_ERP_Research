"""
Account Payable (Open AP Subledger) Extractor
Target Table: "EVA_BI"."ACCOUNT_PAYABLE"
Target Temp Table: "EVA_BI"."ACCOUNT_PAYABLE_TEMP"
Source Model: "account.move.line" (posted payable lines with residual != 0)
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


class AccountPayableExtractor(BaseExtractor):
    """
    Extracts open accounts payable balances and vendor aging buckets.
    """
    target_table = "ACCOUNT_PAYABLE"
    procedure_name = "sp_update_account_payable"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 5000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("parent_state", "=", "posted"),
            ("account_id.account_type", "=", "liability_payable"),
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
            bill_num = move_display.split()[0] if move_display else "NA"

            bill_date_str = line.get("date")
            bill_date = parse_date(bill_date_str)
            due_date = parse_date(line.get("date_maturity")) or bill_date

            credit = safe_num(line.get("credit"))
            debit = safe_num(line.get("debit"))
            bill_amount = credit if credit > 0 else (credit - debit)
            # In Odoo, payable residual is typically negative; make positive for reporting
            outstanding = abs(safe_num(line.get("amount_residual")))
            amount_paid = bill_amount - outstanding

            aging_days = 0
            if bill_date_str:
                try:
                    dt = datetime.strptime(bill_date_str[:10], "%Y-%m-%d").date()
                    aging_days = max(0, (today - dt).days)
                except Exception:
                    aging_days = 0

            d1 = outstanding if aging_days <= 30 else 0.0
            d2 = outstanding if 31 <= aging_days <= 60 else 0.0
            d3 = outstanding if 61 <= aging_days <= 90 else 0.0
            d4 = outstanding if 91 <= aging_days <= 120 else 0.0
            d5 = outstanding if aging_days > 120 else 0.0

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "VOUCHER_NUMBER": bill_num,
                "VOUCHER_DATE": bill_date,
                "ACCOUNT_CODE": account_id,
                "INVOICE_NUMBER": bill_num,
                "INVOICE_DATE": bill_date,
                "DUE_DATE": due_date,
                "OUTSTANDING_DATE": snapshot.strftime("%Y-%m-%d %H:%M:%S"),
                "INVOICE_AMOUNT": bill_amount,
                "OUTSTANDING": outstanding,
                "CURRENCY_CODE": 1,
                "AMOUNT_PAID": amount_paid,
                "OUTSTANDING_DAYS": aging_days,
                "REGION": "NA",
                "INVOICE_AMOUNT_BASE": bill_amount,
                "INVOICE_AMOUNT_REPORTING": bill_amount,
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

