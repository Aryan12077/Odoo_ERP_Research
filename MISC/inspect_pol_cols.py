import csv

with open("odoo_table_column_metadata.csv", "r", encoding="utf-8") as f:
    pol = [r for r in csv.DictReader(f) if r["table_name"] == "purchase_order_line"]

print(f"Total purchase_order_line columns: {len(pol)}")
for r in sorted(pol, key=lambda x: x["column_name"]):
    print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

