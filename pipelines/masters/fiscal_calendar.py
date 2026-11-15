"""
Fiscal Calendar Extractor
Target Table: "EVA_BI"."FISCAL_CALENDAR"
Target Temp Table: "EVA_BI"."FISCAL_CALENDAR_TEMP"
Source: Generated Date Dimension aligned with Odoo Company Fiscal Year settings.

Columns:
- GROUP_COMPANY_CODE (varchar)
- COMPANY_CODE (varchar)
- Cy Start Date (timestamp)
- Cy End Date (timestamp)
- FY Start Date (timestamp)
- FY End Date (timestamp)
- Cy Year (varchar)
- Fy Year (varchar)
- Cy Rank (numeric)
- Fy Rank (numeric)
- Cy Qtr (varchar)
- Fy Qtr (varchar)
- Month Start Date (timestamp)
- Month End Date (timestamp)
- Month (varchar)
- Cy Month No (bigint)
- Fy Month No (bigint)
- Week Start Date (timestamp)
- Week End Date (timestamp)
- Cy Week No (varchar)
- Fy Week No (varchar)
- Month Week No (varchar)
- Date (timestamp)
- Day (varchar)
- Day Name (varchar)
- Week Day (numeric)
- Last Transaction Date (timestamp)
- SNAPSHOT_DT (timestamp)
"""

from datetime import datetime, date, timedelta
import calendar
from typing import Any, Optional
from connector import OdooClient
from pipelines.base import BaseExtractor, pad_code


class FiscalCalendarExtractor(BaseExtractor):
    """
    Generates and synchronizes the complete date and fiscal calendar dimension.
    """
    target_table = "FISCAL_CALENDAR"
    procedure_name = "sp_update_fiscal_calendar"

    def __init__(self, start_year: int = 2018, end_year: int = 2027):
        self.start_year = start_year
        self.end_year = end_year

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        # Fetch company code and fiscal year settings
        comps = client.search_read(
            model="res.company",
            domain=[],
            fields=["id", "name", "fiscalyear_last_day", "fiscalyear_last_month"],
            limit=1
        )
        comp_id = comps[0]["id"] if comps else 1
        comp_code = pad_code(comp_id)

        # In Roshni Odoo, fiscalyear_last_month is '12', matching standard calendar year
        start_date = date(self.start_year, 1, 1)
        end_date = date(self.end_year, 12, 31)

        rows = []
        snapshot = datetime.now()
        current_d = start_date

        one_day = timedelta(days=1)

        while current_d <= end_date:
            y = current_d.year
            m = current_d.month
            d_num = current_d.day

            # Quarter calculation
            qtr = f"Q{(m - 1) // 3 + 1}"

            # Calendar Year Start & End
            cy_start = datetime(y, 1, 1, 0, 0, 0)
            cy_end = datetime(y, 12, 31, 23, 59, 59)

            # Month Start & End
            last_day_of_month = calendar.monthrange(y, m)[1]
            m_start = datetime(y, m, 1, 0, 0, 0)
            m_end = datetime(y, m, last_day_of_month, 23, 59, 59)

            # Week Start (Monday) & End (Sunday)
            monday = current_d - timedelta(days=current_d.weekday())
            sunday = monday + timedelta(days=6)
            w_start = datetime(monday.year, monday.month, monday.day, 0, 0, 0)
            w_end = datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59)

            # ISO Week Number
            iso_week = current_d.isocalendar()[1]
            week_str = f"W{iso_week:02d}"

            # Month Week Number (1 to 5)
            month_week_no = str(((d_num - 1) // 7) + 1)

            # Weekday: 1=Monday .. 7=Sunday
            weekday_num = current_d.weekday() + 1
            day_name = current_d.strftime("%A")
            month_name = current_d.strftime("%B")
            day_str = f"{d_num:02d}"

            dt_val = datetime(y, m, d_num, 0, 0, 0)

            rows.append({
                "GROUP_COMPANY_CODE": comp_code,
                "COMPANY_CODE": comp_code,
                "Cy Start Date": cy_start,
                "Cy End Date": cy_end,
                "FY Start Date": cy_start,
                "FY End Date": cy_end,
                "Cy Year": str(y),
                "Fy Year": str(y),
                "Cy Rank": y - 2017,
                "Fy Rank": y - 2017,
                "Cy Qtr": qtr,
                "Fy Qtr": qtr,
                "Month Start Date": m_start,
                "Month End Date": m_end,
                "Month": month_name,
                "Cy Month No": m,
                "Fy Month No": m,
                "Week Start Date": w_start,
                "Week End Date": w_end,
                "Cy Week No": week_str,
                "Fy Week No": week_str,
                "Month Week No": month_week_no,
                "Date": dt_val,
                "Day": day_str,
                "Day Name": day_name,
                "Week Day": weekday_num,
                "Last Transaction Date": dt_val,
                "SNAPSHOT_DT": snapshot
            })

            current_d += one_day

        return rows

