import json

with open("MISC/table_columns_audit.json", "r", encoding="utf-8") as f:
    old_audit = json.load(f)

with open("MISC/roshni_new_summary.json", "r", encoding="utf-8") as f:
    new_summary = json.load(f)

# Build a lookup for old_audit: table_name -> {total_rows, col_map}
old_map = {}
for tbl_name, info in old_audit.items():
    clean_k = tbl_name.split(".")[-1].upper()
    col_map = {}
    for c in info.get("cols", []):
        col_map[c["column"]] = c
    old_map[clean_k] = {
        "total_rows": info.get("total_rows", 0),
        "columns": col_map
    }

print("=" * 80)
print(f"{'TABLE NAME':<25} | {'OLD ROWS':<10} | {'NEW ROWS':<10} | {'ROW DELTA':<10} | {'STATUS'}")
print("=" * 80)

for full_tbl, new_info in sorted(new_summary.items()):
    if full_tbl.endswith("_TEMP"):
        continue
    tbl = full_tbl.split(".")[-1].upper()
    new_rows = new_info["row_count"]
    old_info = old_map.get(tbl)
    old_rows = old_info["total_rows"] if old_info else 0
    delta = new_rows - old_rows
    status = "NEW TABLE (ADDED)" if old_rows == 0 else ("ROWS CHANGED" if delta != 0 else "MATCH")
    print(f"{tbl:<25} | {old_rows:<10} | {new_rows:<10} | {delta:+<10} | {status}")

print("\n" + "=" * 80)
print("DEEP-DIVE COLUMN COMPARISON FOR TARGET ENRICHMENTS")
print("=" * 80)

check_specs = {
    "SALES_DATA": ["STORE_ID", "WAREHOUSE_ID", "EXECUTIVE_ID", "EXECUTIVE", "COGS_USD", "COGS_AUD"],
    "PURCHASE_DATA": ["GRN_NUMBER", "BILL_NUMBER", "WAREHOUSE_ID", "LEAD_TIME"],
    "PRODUCT_MASTER": ["STOCK_QUANTITY", "SUPPLIER", "LEAD_TIME_IN_DAYS"],
    "ACCOUNT_RECEIVABLE": ["REGION", "CUSTOMER_CATEGORY"],
    "ACCOUNT_PAYABLE": ["REGION", "CUSTOMER_CATEGORY"],
    "GEO_MASTER": ["STORE_ID", "STORE_NAME", "WAREHOUSE_ID", "WAREHOUSE_NAME", "BRANCH_NAME"],
    "FISCAL_CALENDAR": ["Calender Date", "Financial Year", "Financial Quarter", "Financial Month"],
    "ANALYSIS_CRITERIA": ["Analysis Code", "Analysis Criteria", "Currency Code", "Currency"]
}

detailed_findings = {}

for tbl_name, target_cols in check_specs.items():
    full_tbl = f"EBIZFRAME_BI.{tbl_name}"
    new_info = new_summary.get(full_tbl)
    old_info = old_map.get(tbl_name)
    
    print(f"\n=======================================================")
    print(f"TABLE: {tbl_name}")
    print(f"=======================================================")
    if not new_info:
        print("  Not found in new backup!")
        continue
    
    new_rows = new_info["row_count"]
    old_rows = old_info["total_rows"] if old_info else 0
    print(f"Total Rows: Old = {old_rows}, New = {new_rows}")
    
    table_findings = []
    
    for col in target_cols:
        new_stats = new_info["col_stats"].get(col, {})
        old_stats = old_info["columns"].get(col, {}) if old_info and "columns" in old_info else {}
        
        # New stats
        new_pop = new_stats.get("populated_count", 0)
        new_null = new_stats.get("null_count", 0)
        new_na = new_stats.get("na_count", 0)
        new_zero = new_stats.get("zero_count", 0)
        new_samples = new_stats.get("distinct_samples", [])
        
        # Old stats
        old_null = old_stats.get("null_count", 0)
        old_na = old_stats.get("na_count", 0)
        old_zero = old_stats.get("zero_count", 0)
        old_samples = old_stats.get("samples", [])
        
        print(f"\n  >> Column: [{col}]")
        print(f"     OLD: null={old_null}, 'NA'={old_na}, zero={old_zero}, samples={old_samples[:3]}")
        print(f"     NEW: null={new_null}, 'NA'={new_na}, zero={new_zero}, populated={new_pop}/{new_rows}")
        print(f"          samples={new_samples[:5]}")
        
        table_findings.append({
            "column": col,
            "old_stats": {"null": old_null, "na": old_na, "zero": old_zero, "samples": old_samples},
            "new_stats": {"null": new_null, "na": new_na, "zero": new_zero, "populated": new_pop, "samples": new_samples}
        })
    detailed_findings[tbl_name] = table_findings

with open("MISC/backup_comparison_details.json", "w", encoding="utf-8") as out:
    json.dump(detailed_findings, out, indent=2)

print("\nDetails saved to MISC/backup_comparison_details.json")
