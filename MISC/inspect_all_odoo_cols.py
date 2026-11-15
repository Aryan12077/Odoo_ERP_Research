import pandas as pd

df = pd.read_csv('odoo_table_column_metadata.csv')

def get_table_cols(tbl):
    sub = df[df['table_name'] == tbl]
    return dict(zip(sub['column_name'], sub['column_description']))

models = df['table_name'].unique()
print("Available models:", list(models))

# Let's inspect specific models
for m in ['res_company', 'res_partner', 'res_currency', 'account_account', 'product_template', 'product_product', 'sale_order', 'sale_order_line', 'purchase_order', 'purchase_order_line', 'stock_warehouse', 'stock_quant', 'account_move', 'account_move_line', 'account_payment']:
    cols = get_table_cols(m)
    print(f"\n--- {m} ({len(cols)} cols) ---")
    # print first 10
    for k, v in list(cols.items())[:15]:
        print(f"  {k}: {v}")

