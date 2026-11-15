import pandas as pd
df = pd.read_csv('odoo_table_column_metadata.csv')
ac = df[df['table_name'] == 'account_account']
for _, r in ac.iterrows():
    print(r['column_name'], '|', r['column_datatype'], '|', r['column_description'])

