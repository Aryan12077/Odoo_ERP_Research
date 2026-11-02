import csv

with open("odoo_table_column_metadata.csv", "r", encoding="utf-8") as f:
    rows = [r for r in csv.DictReader(f) if r["table_name"] == "product_template"]

for r in sorted(rows, key=lambda x: x["column_name"]):
    cname = r["column_name"]
    cdesc = r["column_description"]
    ctype = r["column_datatype"]
    for keyword in ["brand", "weight", "uom", "price", "cost", "categ", "seller", "supplier", "code", "barcode", "type", "tax", "volume"]:
        if keyword in cname.lower() or keyword in cdesc.lower():
            print(f"  {cname} ({ctype}): {cdesc}")
            break

