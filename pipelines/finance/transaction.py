"""
General Ledger Transaction Extractor
Target Table: "EVA_BI"."TRANSACTION"
Target Temp Table: "EVA_BI"."TRANSACTION_TEMP"
Source Model: "account.move.line" (posted journal items)

Columns:
- GROUP_COMPANY_CODE (varchar)
- COMPANY_CODE (varchar)
- BRANCH_ID (varchar)
- ACCOUNT_CODE (integer)
- VOUCHER_NUMBER (varchar)
- VOUCHER_DATE (timestamp)
- AMOUNT (numeric)
- AMOUNT_BASE (numeric)
- SERIAL_NUMBER (numeric)
- TRANSACTION_TYPE (varchar)
- TRANSACTION_TYPE_BASE (varchar)
- AUTHORIZATION_FLAG (varchar)
- VOUCHER_TYPE (varchar)
- DUE_DATE (timestamp)
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


class TransactionExtractor(BaseExtractor):
    """
    Extracts all posted financial journal items (GL transactions).
    """
    target_table = "TRANSACTION"
    procedure_name = "sp_update_transaction"

    def __init__(self, domain: Optional[list] = None, batch_limit: int = 10000):
        self.custom_domain = domain
        self.batch_limit = batch_limit

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        base_domain = [
            ("parent_state", "=", "posted")
        ]
        if self.custom_domain:
            base_domain.extend(self.custom_domain)

        fields = [
            "id",
            "move_id",
            "date",
            "account_id",
            "debit",
            "credit",
            "balance",
            "journal_id",
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
        snapshot = datetime.now()

        for idx, line in enumerate(lines, start=1):
            comp_id = get_m2o_id(line.get("company_id")) or 1
            comp_code = pad_code(comp_id)

            account_id = get_m2o_id(line.get("account_id"))
            move_display = get_m2o_name(line.get("move_id"), "")
            voucher_num = move_display.split()[0] if move_display else "NA"
            voucher_type = get_m2o_name(line.get("journal_id"), "General")

            debit = safe_num(line.get("debit"))
            credit = safe_num(line.get("credit"))
            is_debit = debit > 0 or debit >= credit
            amount = debit if is_debit else credit
            tx_type = "DEBIT" if is_debit else "CREDIT"

            voucher_date = parse_date(line.get("date"))
            due_date = parse_date(line.get("date_maturity")) or voucher_date

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "ACCOUNT_CODE": account_id,
                "VOUCHER_NUMBER": voucher_num,
                "VOUCHER_DATE": voucher_date,
                "AMOUNT": amount,
                "AMOUNT_BASE": amount,
                "SERIAL_NUMBER": idx,
                "TRANSACTION_TYPE": tx_type,
                "TRANSACTION_TYPE_BASE": tx_type,
                "AUTHORIZATION_FLAG": "Y",
                "VOUCHER_TYPE": voucher_type,
                "DUE_DATE": due_date,
                "SNAPSHOT_DT": snapshot
            })

        return rows

