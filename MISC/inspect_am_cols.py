import csv

with open("odoo_table_column_metadata.csv", "r", encoding="utf-8") as f:
    rows = [r for r in csv.DictReader(f) if r["table_name"] == "account_move"]

print(f"Total account_move columns: {len(rows)}")
for r in sorted(rows, key=lambda x: x["column_name"]):
    print(f"  {r['column_name']} ({r['column_datatype']}): {r['column_description']}")

