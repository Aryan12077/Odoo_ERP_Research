import re

with open("DAL_BKP_08042026", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

procs = re.findall(r'CREATE (?:OR REPLACE )?PROCEDURE [^\(]*?"?([A-Za-z0-9_]+)"?\s*\((.*?)\)\s+LANGUAGE [^\n]+\s+AS \$\$([\s\S]*?)\$\$;', text)

for name, args, body in procs:
    m = re.search(r'DELETE FROM [^\n]+WHERE (.*?)(?:;|\n\s*INSERT)', body, re.DOTALL | re.IGNORECASE)
    where_clause = m.group(1).strip() if m else "NO WHERE FOUND"
    # Compact where clause
    where_compact = " ".join(where_clause.split())
    print(f"{name:30}: {where_compact}")

