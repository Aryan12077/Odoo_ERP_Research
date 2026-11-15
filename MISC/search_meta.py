import pandas as pd

df = pd.read_csv('odoo_table_column_metadata.csv')

def search_cols(model_substr, col_substr=None):
    res = df[df['table_name'].str.contains(model_substr, case=False, na=False)]
    if col_substr:
        res = res[res['column_name'].str.contains(col_substr, case=False, na=False) | res['column_description'].str.contains(col_substr, case=False, na=False)]
    return res[['table_name', 'column_name', 'column_description', 'column_datatype']]

print("Total columns in metadata:", len(df))
print("Models available:", df['table_name'].unique().tolist())

