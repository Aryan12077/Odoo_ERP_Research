import re
import json

file_path = "roshni_new.sql"

# Let's inspect COPY blocks in roshni_new.sql
copy_pattern = re.compile(r'^COPY\s+([^\s]+)\s*\((.*?)\)\s+FROM\s+stdin;', re.IGNORECASE)

tables_data = {}

current_table = None
current_cols = []
current_rows = []

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if line.startswith(r'\.'):
            if current_table:
                tables_data[current_table] = {
                    "columns": current_cols,
                    "row_count": len(current_rows),
                    "sample_rows": current_rows[:3] if current_rows else [],
                    "all_rows": current_rows
                }
                current_table = None
                current_cols = []
                current_rows = []
            continue

        if current_table:
            # tab separated values in pg_dump
            parts = line.rstrip('\r\n').split('\t')
            current_rows.append(parts)
            continue

        m = copy_pattern.match(line)
        if m:
            full_table = m.group(1).replace('"', '')
            cols_str = m.group(2)
            cols = [c.strip().replace('"', '') for c in cols_str.split(',')]
            current_table = full_table
            current_cols = cols
            current_rows = []

print(f"Found {len(tables_data)} tables with COPY data:")
for tbl, info in sorted(tables_data.items()):
    print(f"  {tbl}: {info['row_count']} rows, {len(info['columns'])} cols")

# Save summary without full row text to avoid massive json
summary = {}
for tbl, info in tables_data.items():
    # Analyze nulls/stubs per column
    col_stats = {}
    cols = info["columns"]
    total = info["row_count"]
    
    for i, col in enumerate(cols):
        null_count = 0
        na_count = 0
        zero_count = 0
        distinct_vals = set()
        
        for row in info["all_rows"]:
            if i < len(row):
                val = row[i]
                if val == r'\N' or val == '':
                    null_count += 1
                elif val.strip().upper() == 'NA':
                    na_count += 1
                elif val.strip() in ('0', '0.0', '0.00', '0.0000'):
                    zero_count += 1
                if len(distinct_vals) < 5:
                    distinct_vals.add(val)
        
        col_stats[col] = {
            "null_count": null_count,
            "na_count": na_count,
            "zero_count": zero_count,
            "distinct_samples": list(distinct_vals)[:5],
            "populated_count": total - null_count - na_count
        }

    summary[tbl] = {
        "columns": cols,
        "row_count": total,
        "col_stats": col_stats,
        "sample_row": info["sample_rows"][0] if info["sample_rows"] else []
    }

with open("MISC/roshni_new_summary.json", "w", encoding="utf-8") as out:
    json.dump(summary, out, indent=2)

print("\nSummary saved to MISC/roshni_new_summary.json")

