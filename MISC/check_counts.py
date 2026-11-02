from db_loader import DWHLoader

loader = DWHLoader()
with loader.get_connection() as conn:
    with conn.cursor() as cur:
        for t in ["COMPANY_MASTER", "BRANCH_MASTER", "CURRENCY_MASTER", "CHART_OF_ACCOUNT", "ACCOUNT_TYPE", "CUSTOMER_MASTER", "SUPPLIER_MASTER", "PRODUCT_MASTER", "SALES_DATA", "MONTHLY_SALE", "PURCHASE_DATA", "MONTHLY_PURCHASE", "INVENTORY_AGEING", "TRANSACTION", "ACCOUNT_RECEIVABLE", "ACCOUNT_PAYABLE", "MONTHLY_COLLECTION", "MONTHLY_PAYMENT"]:
            cur.execute(f'SELECT COUNT(*) FROM "odoo_roshni"."{t}";')
            cnt = cur.fetchone()[0]
            print(f"{t:22}: {cnt} rows")

