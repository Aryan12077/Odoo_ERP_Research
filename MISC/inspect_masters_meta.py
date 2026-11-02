import csv

with open("odoo_table_column_metadata.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

def list_all_cols(table_name):
    print(f"\n=================== TABLE: {table_name} ===================")
    trows = [r for r in rows if r["table_name"] == table_name]
    for r in sorted(trows, key=lambda x: x["column_name"]):
        print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

list_all_cols("res_company")
list_all_cols("stock_warehouse")
list_all_cols("product_category")
list_all_cols("account_account")
list_all_cols("account_group")

