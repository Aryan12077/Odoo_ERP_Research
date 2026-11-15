import re

with open('Table_references.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

for tbl in ['GEO_MASTER', 'FISCAL_CALENDAR', 'ANALYSIS_CRITERIA']:
    pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\(]*?' + tbl + r'[\"\s]*)\((.*?)\);'
    m = re.search(pattern, sql, re.DOTALL | re.IGNORECASE)
    if m:
        print(f"=== TABLE DEFINITION: {tbl} ===")
        print(m.group(0))
        print()
    else:
        print(f"Table {tbl} not found in Table_references.sql\n")

# Check if stored procedures or temp tables exist for them
for tbl in ['GEO_MASTER', 'FISCAL_CALENDAR', 'ANALYSIS_CRITERIA']:
    proc_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+([^\(]*?sp_update_' + tbl.lower() + r'[\"\s]*)\((.*?)\)\s+LANGUAGE.*?\$\$;'
    m_proc = re.search(proc_pattern, sql, re.DOTALL | re.IGNORECASE)
    if m_proc:
        print(f"=== PROCEDURE: sp_update_{tbl.lower()} FOUND! ===")
        print(m_proc.group(0)[:300])
        print("...")
    else:
        print(f"Procedure sp_update_{tbl.lower()} NOT found in Table_references.sql")

