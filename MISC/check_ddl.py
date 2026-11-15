import re

with open('Table_references.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

# Find all CREATE TABLE statements
tables = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s\(]+)\s*\((.*?)\);', sql, re.DOTALL | re.IGNORECASE)

print(f"Found {len(tables)} tables in Table_references.sql:")
for t_name, cols_def in tables:
    col_lines = [l.strip() for l in cols_def.strip().split('\n') if l.strip() and not l.strip().startswith('--')]
    cols = []
    for cl in col_lines:
        m = re.match(r'\"?([a-zA-Z0-9_\s]+)\"?\s+([a-zA-Z0-9_\(\)]+)', cl)
        if m:
            cols.append((m.group(1).strip(), m.group(2).strip()))
    print(f"Table: {t_name.strip()} ({len(cols)} columns)")

