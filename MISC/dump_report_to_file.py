import json

with open('MISC/backup_analysis_summary.json', 'r') as f:
    summary = json.load(f)

with open('MISC/missing_analysis_full.txt', 'w', encoding='utf-8') as out_f:
    for table, data in sorted(summary.items()):
        n_rows = data['total_rows']
        out_f.write("==================================================\n")
        out_f.write(f"TABLE: {table} (Rows: {n_rows})\n")
        out_f.write("==================================================\n")
        if n_rows == 0:
            out_f.write("  Table has 0 rows in backup.\n")
            out_f.write(f"  Columns defined ({len(data['cols'])}): {list(data['cols'].keys())}\n\n")
            continue

        for col, stat in data['cols'].items():
            n = stat['null']
            na = stat['na']
            e = stat['empty']
            z = stat['zero']
            v = stat['valid']
            pct = stat['pct_missing']
            sample = stat['sample'][:2]
            
            if pct == 100.0:
                out_f.write(f"  [MISSING 100%] {col:30} | Null: {n:5} | NA: {na:5} | Empty: {e:5} | Zero: {z:5}\n")
            elif pct > 0:
                out_f.write(f"  [PARTIAL {pct:5.1f}%] {col:30} | Valid: {v:5} | Null: {n:5} | NA: {na:5} | Sample: {sample}\n")
            elif z == n_rows:
                out_f.write(f"  [ALL ZEROS   ] {col:30} | Zero: {z:5}\n")
            else:
                out_f.write(f"  [POPULATED   ] {col:30} | Valid: {v:5} | Sample: {sample}\n")
        out_f.write("\n")

print("Done writing MISC/missing_analysis_full.txt")

