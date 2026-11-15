import json

with open("MISC/roshni_new_summary.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 80)
print("AUDIT OF UNPOPULATED (100% NULL OR 100% 'NA') COLUMNS IN roshni_new.sql")
print("=" * 80)

for tbl_name, info in sorted(data.items()):
    if tbl_name.endswith("_TEMP"):
        continue
    total_rows = info["row_count"]
    if total_rows == 0:
        continue
    
    unpopulated_cols = []
    partially_populated = []
    fully_populated = []
    
    for col, stats in info["col_stats"].items():
        pop = stats["populated_count"]
        null_cnt = stats["null_count"]
        na_cnt = stats["na_count"]
        zero_cnt = stats["zero_count"]
        
        if pop == 0 and (null_cnt == total_rows or na_cnt == total_rows):
            unpopulated_cols.append((col, "100% NULL" if null_cnt == total_rows else "100% 'NA'"))
        elif pop < total_rows:
            partially_populated.append((col, pop, total_rows))
        else:
            fully_populated.append(col)
            
    print(f"\nTABLE: {tbl_name} ({total_rows} rows)")
    print(f"  Fully Populated Columns: {len(fully_populated)} / {len(info['columns'])}")
    if partially_populated:
        print(f"  Partially Populated Columns ({len(partially_populated)}):")
        for col, pop, tot in partially_populated[:10]:
            print(f"    - {col}: {pop}/{tot} ({pop/tot*100:.1f}%)")
        if len(partially_populated) > 10:
            print(f"    ... and {len(partially_populated)-10} more")
    if unpopulated_cols:
        print(f"  100% Stubbed/Empty Columns ({len(unpopulated_cols)}):")
        for col, reason in unpopulated_cols:
            print(f"    - {col}: {reason}")

