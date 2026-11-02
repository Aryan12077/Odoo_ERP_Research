"""
Monthly Payment Aggregator
Target Table: "EVA_BI"."MONTHLY_PAYMENT"
Target Temp Table: "EVA_BI"."MONTHLY_PAYMENT_TEMP"
Source Model: "account.move.line" (debits on liability_payable accounts, aggregated by month & vendor)

Columns:
- GROUP_COMPANY_CODE (varchar)
- COMPANY_CODE (varchar)
- BRANCH_ID (varchar)
- ACCOUNT_CODE (integer)
- FOR_MONTH (timestamp)
- PAYMENT (numeric)
- PAYMENT_BASE (numeric)
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
)


class MonthlyPaymentExtractor(BaseExtractor):
    """
    Extracts and aggregates vendor disbursements/payments by month.
    """
    target_table = "MONTHLY_PAYMENT"
    procedure_name = "sp_update_monthly_payment"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 10000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("parent_state", "=", "posted"),
            ("account_id.account_type", "=", "liability_payable"),
            ("debit", ">", 0),
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "date",
            "partner_id",
            "account_id",
            "debit",
            "company_id"
        ]

        lines = client.search_read(
            model="account.move.line",
            domain=base_domain,
            fields=fields,
            limit=self.batch_limit,
            order="date desc, id desc"
        )

        grouped = defaultdict(float)

        for line in lines:
            dt_str = line.get("date")
            if not dt_str:
                continue

            for_month = f"{dt_str[:7]}-01 00:00:00"
            comp_id = get_m2o_id(line.get("company_id")) or 1
            partner_id = get_m2o_id(line.get("partner_id")) or 0
            debit = safe_num(line.get("debit"))

            key = (comp_id, partner_id, for_month)
            grouped[key] += debit

        rows = []
        snapshot = datetime.now()

        for (comp_id, partner_id, for_month), total_payment in grouped.items():
            code = pad_code(comp_id)
            rounded = round(total_payment, 2)
            rows.append({
                "GROUP_COMPANY_CODE": code,
                "COMPANY_CODE": code,
                "BRANCH_ID": code,
                "ACCOUNT_CODE": partner_id,
                "FOR_MONTH": for_month,
                "PAYMENT": rounded,
                "PAYMENT_BASE": rounded,
                "SNAPSHOT_DT": snapshot
            })

        return rows

