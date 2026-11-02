from db_loader import DWHLoader

loader = DWHLoader()
with loader.get_connection() as conn:
    with conn.cursor() as cur:
        print("=== Latest SALES_DATA ===")
        cur.execute('SELECT "INVOICE_NUMBER", "CUSTOMER_CODE", "PRODUCT_CODE", "EXECUTIVE_ID", "EXECUTIVE", "SNAPSHOT_DT" FROM "odoo_roshni"."SALES_DATA" ORDER BY "SNAPSHOT_DT" DESC LIMIT 5;')
        for r in cur.fetchall():
            print(" ", r)

        print("\n=== Latest PURCHASE_DATA ===")
        cur.execute('SELECT "PURCHASE_ORDER_NUMBER", "SUPPLIER_CODE", "ITEM_CODE", "WAREHOUSE_ID", "GRN_NUMBER", "BILL_NUMBER", "SNAPSHOT_DT" FROM "odoo_roshni"."PURCHASE_DATA" ORDER BY "SNAPSHOT_DT" DESC LIMIT 5;')
        for r in cur.fetchall():
            print(" ", r)

        print("\n=== Latest PRODUCT_MASTER ===")
        cur.execute('SELECT "PRODUCT_CODE", "PRODUCT", "GROUP_NAME", "SUB_GROUP", "SUB_SUB_GROUP", "SNAPSHOT_DT" FROM "odoo_roshni"."PRODUCT_MASTER" ORDER BY "SNAPSHOT_DT" DESC LIMIT 5;')
        for r in cur.fetchall():
            print(" ", r)

        print("\n=== Latest INVENTORY_AGEING ===")
        cur.execute('SELECT "PRODUCT_CODE", "WAREHOUSE_ID", "REMAINING_QUANTITY", "ITEM_UNIT_COST_USD", "SNAPSHOT_DT" FROM "odoo_roshni"."INVENTORY_AGEING" ORDER BY "SNAPSHOT_DT" DESC LIMIT 5;')
        for r in cur.fetchall():
            print(" ", r)
