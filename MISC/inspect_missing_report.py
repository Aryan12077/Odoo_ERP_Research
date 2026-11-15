import json

with open('MISC/backup_analysis_summary.json', 'r') as f:
    summary = json.load(f)

for table, data in sorted(summary.items()):
    n_rows = data['total_rows']
    print(f"==================================================")
    print(f"TABLE: {table} (Rows: {n_rows})")
    print(f"==================================================")
    if n_rows == 0:
        print("  Table has 0 rows in backup.")
        print(f"  Columns defined ({len(data['cols'])}): {list(data['cols'].keys())}\n")
        continue

    for col, stat in data['cols'].items():
        n = stat['null']
        na = stat['na']
        e = stat['empty']
        z = stat['zero']
        v = stat['valid']
        pct = stat['pct_missing']
        sample = stat['sample'][:2]
        
        # Categorize
        if pct == 100.0:
            status = "100% MISSING"
            print(f"  [MISSING 100%] {col:30} | Null: {n:5} | NA: {na:5} | Empty: {e:5} | Zero: {z:5}")
        elif pct > 0:
            status = f"PARTIAL ({pct}%)"
            print(f"  [PARTIAL {pct:5.1f}%] {col:30} | Valid: {v:5} | Null: {n:5} | NA: {na:5} | Sample: {sample}")
        elif z == n_rows:
            print(f"  [ALL ZEROS   ] {col:30} | Zero: {z:5}")
        else:
            # Fully populated
            pass
    print()
