import pandas as pd

df = pd.read_csv('odoo_table_column_metadata.csv')
pt_cols = df[df['table_name'].isin(['product_template', 'product_product'])]

keywords = ['brand', 'oem', 'make', 'part', 'size', 'categ', 'sub', 'sale', 'purchase', 'order', 'qty', 'stock', 'reorder', 'min', 'max', 'supplier', 'seller', 'vendor', 'lead', 'cost', 'price', 'weight', 'volume', 'uom', 'tax', 'barcode', 'code']

matches = []
for kw in keywords:
    sub = pt_cols[pt_cols['column_name'].str.contains(kw, case=False) | pt_cols['column_description'].str.contains(kw, case=False)]
    for _, r in sub.iterrows():
        matches.append((r['table_name'], r['column_name'], r['column_description'], r['column_datatype']))

matches = list(set(matches))
print(f"Found {len(matches)} matching columns in product_template & product_product:")
for t, c, d, dt in sorted(matches):
    print(f"  [{t:16}] {c:32} | {dt:12} | {d}")

