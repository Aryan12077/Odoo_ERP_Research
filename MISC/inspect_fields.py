import csv

with open("odoo_table_column_metadata.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

def find_columns(table_name, search_terms=None):
    res = [r for r in rows if r["table_name"] == table_name]
    if search_terms:
        res = [r for r in res if any(term.lower() in r["column_name"].lower() or term.lower() in r["column_description"].lower() for term in search_terms)]
    return res

print("=== account_move_line ===")
for r in find_columns("account_move_line", ["user", "sale", "order", "warehouse", "cost", "cogs"]):
    print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

print("\n=== account_move ===")
for r in find_columns("account_move", ["user", "sale", "order", "warehouse", "partner"]):
    print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

print("\n=== purchase_order_line ===")
for r in find_columns("purchase_order_line", ["order", "date", "picking", "invoice", "move", "warehouse"]):
    print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

print("\n=== purchase_order ===")
for r in find_columns("purchase_order", ["picking", "invoice", "warehouse", "user", "dest"]):
    print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

print("\n=== res_partner ===")
for r in find_columns("res_partner", ["category", "user", "industry", "title", "type"]):
    print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

print("\n=== stock_quant ===")
for r in find_columns("stock_quant", ["warehouse", "location", "lot", "package", "owner"]):
    print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

