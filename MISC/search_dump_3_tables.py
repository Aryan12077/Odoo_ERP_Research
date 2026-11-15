tables = ['GEO_MASTER', 'FISCAL_CALENDAR', 'ANALYSIS_CRITERIA']
mentions = {t: [] for t in tables}

with open('odoo_roshni_bkp_local_2.sql', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f):
        for t in tables:
            if t in line:
                if any(kw in line.upper() for kw in ['CREATE ', 'PROCEDURE', 'COPY ', 'INSERT ', 'TABLE ']):
                    mentions[t].append((idx + 1, line.strip()))

for t in tables:
    print(f"=== {t} ({len(mentions[t])} structural lines) ===")
    for line_num, l in mentions[t]:
        print(f"  Line {line_num}: {l}")
    print()
