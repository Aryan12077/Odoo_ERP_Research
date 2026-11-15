import pandas as pd

df = pd.read_csv('odoo_table_column_metadata.csv')
p_cols = df[df['table_name'] == 'res_partner']

search_terms = ['credit', 'term', 'limit', 'categ', 'type', 'account', 'currency', 'zone', 'region', 'area', 'industry', 'payment', 'phone', 'mobile']

matches = []
for term in search_terms:
    sub = p_cols[p_cols['column_name'].str.contains(term, case=False) | p_cols['column_description'].str.contains(term, case=False)]
    for _, r in sub.iterrows():
        matches.append((r['column_name'], r['column_description'], r['column_datatype']))

matches = list(set(matches))
print(f"Found {len(matches)} matching columns in res_partner:")
for c, d, dt in sorted(matches):
    print(f"  {c:35} | {dt:15} | {d}")

