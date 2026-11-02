"""
Chart of Accounts & Account Type Extractor
Target Tables: "EVA_BI"."CHART_OF_ACCOUNT", "EVA_BI"."ACCOUNT_TYPE"
Target Temp Tables: "EVA_BI"."CHART_OF_ACCOUNT_TEMP", "EVA_BI"."ACCOUNT_TYPE_TEMP"
Source Model: "account.account"
"""

from datetime import datetime
from typing import Any
from connector import OdooClient
from pipelines.base import (
    BaseExtractor,
    get_m2o_id,
    pad_code,
)


class ChartOfAccountExtractor(BaseExtractor):
    """
    Extracts Chart of Accounts from Odoo account.account.
    """
    target_table = "CHART_OF_ACCOUNT"
    procedure_name = "sp_update_chart_of_account"

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        accounts = client.search_read(
            model="account.account",
            fields=["id", "code", "name", "account_type", "company_id"]
        )

        rows = []
        snapshot = datetime.now()

        for a in accounts:
            comp_id = get_m2o_id(a.get("company_id")) or 1
            comp_code = pad_code(comp_id)
            code_str = str(a.get("code") or "")
            name_str = f"{code_str} {a.get('name', '')}".strip()

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "GROUP_CODE": "NA",
                "GROUP": a.get("account_type") or "General",
                "S_GROUP_CODE": "NA",
                "S_GROUP": "NA",
                "SS_GROUP_CODE": "NA",
                "SS_GROUP": "NA",
                "SSS_GROUP_CODE": "NA",
                "SSS_GROUP": "NA",
                "SSSS_GROUP_CODE": "NA",
                "SSSS_GROUP": "NA",
                "SSSSS Group Code": "NA",
                "SSSSS_GROUP": "NA",
                "SSSSSS_GROUP_CODE": "NA",
                "SSSSSS_GROUP": "NA",
                "Account Code": a["id"],
                "Account Name": name_str,
                "Ledger Code": code_str or str(a["id"]),
                "SNAPSHOT_DT": snapshot
            })

        return rows


class AccountTypeExtractor(BaseExtractor):
    """
    Extracts Account to Type mappings per account.
    """
    target_table = "ACCOUNT_TYPE"
    procedure_name = "sp_update_account_type"

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        accounts = client.search_read(
            model="account.account",
            fields=["id", "account_type", "company_id"]
        )

        rows = []
        snapshot = datetime.now()

        for a in accounts:
            comp_id = get_m2o_id(a.get("company_id")) or 1
            comp_code = pad_code(comp_id)
            acc_type = a.get("account_type") or "other"

            is_bs = any(k in acc_type for k in ["asset", "liability", "equity"])
            flag = "BS" if is_bs else "PL"

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "BRANCH_ID": comp_code,
                "ACCOUNT_CODE": a["id"],
                "ACCOUNT_TYPE": acc_type.replace("_", " ").title(),
                "ACCOUNT_FLAG": flag,
                "SNAPSHOT_DT": snapshot
            })

        return rows
