import re
import json
import pandas as pd

# 1. Load backup analysis
with open('MISC/backup_analysis_summary.json', 'r') as f:
    backup_summary = json.load(f)

# 2. Load DDL
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

# 3. Load Odoo metadata
odoo_meta = pd.read_csv('odoo_table_column_metadata.csv')

print(f"Loaded {len(ddl_tables)} DDL tables.")
print(f"Loaded {len(backup_summary)} backup tables.")
print(f"Loaded {len(odoo_meta)} Odoo columns.")

# Dump table names
print("\nTables in DDL vs Backup:")
for t in ddl_tables:
    b_rows = backup_summary.get(t, {}).get('total_rows', 'NOT IN BACKUP')
    print(f"  {t:25} | DDL cols: {len(ddl_tables[t]):2} | Backup rows: {b_rows}")

