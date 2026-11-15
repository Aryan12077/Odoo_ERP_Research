import json
import re
import pandas as pd

# Load backup analysis
with open('MISC/backup_analysis_summary.json', 'r') as f:
    backup_summary = json.load(f)

# Load DDL
with open('Table_references.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

ddl_tables = {}
matches = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s\(]+)\s*\((.*?)\);', sql, re.DOTALL | re.IGNORECASE)
for t_raw, cols_raw in matches:
    t_clean = t_raw.replace('"', '').replace('EVA_BI.', '').strip()
    col_lines = [l.strip() for l in cols_raw.strip().split('\n') if l.strip() and not l.strip().startswith('--')]
    cols = []
    for cl in col_lines:
        m = re.match(r'\"?([a-zA-Z0-9_\s]+)\"?\s+([a-zA-Z0-9_\(\)]+)', cl)
        if m:
            cname = m.group(1).strip()
            ctype = m.group(2).strip()
            if cname.upper() not in ('PRIMARY', 'KEY', 'CONSTRAINT', 'UNIQUE'):
                cols.append((cname, ctype))
    ddl_tables[t_clean] = cols

# Load Odoo metadata
odoo_meta = pd.read_csv('odoo_table_column_metadata.csv')

# Let's inspect each table and classify columns
results = {}

for tbl, cols in ddl_tables.items():
    if tbl == 'Data_Push_Agent_Log':
        continue
    tbl_backup = backup_summary.get(tbl, {'total_rows': 0, 'cols': {}})
    n_rows = tbl_backup['total_rows']
    b_cols = tbl_backup['cols']
    
    col_analysis = []
    for cname, ctype in cols:
        b_info = b_cols.get(cname, {})
        null_c = b_info.get('null', 0)
        na_c = b_info.get('na', 0)
        empty_c = b_info.get('empty', 0)
        zero_c = b_info.get('zero', 0)
        valid_c = b_info.get('valid', 0)
        pct_miss = b_info.get('pct_missing', 100.0)
        samples = b_info.get('sample', [])
        
        # determine status in backup
        if n_rows == 0:
            status_in_bkp = "No Rows (Table Empty)"
        elif pct_miss == 100.0:
            status_in_bkp = "100% NA / Missing"
        elif pct_miss > 0:
            status_in_bkp = f"Partially Missing ({pct_miss}%)"
        elif zero_c == n_rows:
            status_in_bkp = "100% Zero / Default"
        else:
            status_in_bkp = "Populated"
            
        col_analysis.append({
            'column': cname,
            'ddl_type': ctype,
            'status_in_bkp': status_in_bkp,
            'valid_count': valid_c,
            'null_count': null_c,
            'na_count': na_c,
            'zero_count': zero_c,
            'samples': samples
        })
    results[tbl] = {
        'total_rows': n_rows,
        'cols': col_analysis
    }

with open('MISC/table_columns_audit.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Saved MISC/table_columns_audit.json")

