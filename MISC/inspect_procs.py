import re

with open("DAL_BKP_08042026", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# Find all procedures: CREATE [OR REPLACE] PROCEDURE <name> ...
procs = re.findall(r'CREATE (?:OR REPLACE )?PROCEDURE [^\(]*?"?([A-Za-z0-9_]+)"?\s*\((.*?)\)\s+LANGUAGE [^\n]+\s+AS \$\$([\s\S]*?)\$\$;', text)

print(f"Found {len(procs)} stored procedures in DAL_BKP_08042026:")
proc_dict = {}
for name, args, body in procs:
    proc_dict[name.lower()] = body
    print(f" - {name}")

# Let's inspect specific procedures
for p in ["sp_update_sales_data", "sp_update_purchase_data", "sp_update_customer_master", "sp_update_product_master", "sp_update_inventory_ageing"]:
    if p in proc_dict:
        print(f"\n================ PROCEDURE: {p} ================")
        # Print first 40 lines of body
        lines = [l for l in proc_dict[p].strip().split("\n") if l.strip() and not l.strip().startswith("--")]
        for l in lines[:30]:
            print("  ", l)

