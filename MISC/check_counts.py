import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_loader import DWHLoader

loader = DWHLoader()
schema = loader.schema
print(f"Target PostgreSQL Schema: \"{schema}\" on {loader.config.host}:{loader.config.port}")
print("-" * 50)

with loader.get_connection() as conn:
    with conn.cursor() as cur:
        total = 0
        for t in ["COMPANY_MASTER", "BRANCH_MASTER", "CURRENCY_MASTER", "CHART_OF_ACCOUNT", "ACCOUNT_TYPE", "CUSTOMER_MASTER", "SUPPLIER_MASTER", "PRODUCT_MASTER", "SALES_DATA", "MONTHLY_SALE", "PURCHASE_DATA", "MONTHLY_PURCHASE", "INVENTORY_AGEING", "TRANSACTION", "ACCOUNT_RECEIVABLE", "ACCOUNT_PAYABLE", "MONTHLY_COLLECTION", "MONTHLY_PAYMENT"]:
            cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{t}";')
            cnt = cur.fetchone()[0]
            total += cnt
            print(f"{t:22}: {cnt} rows")
        print("-" * 50)
        print(f"Total Rows Ingested   : {total} rows")
