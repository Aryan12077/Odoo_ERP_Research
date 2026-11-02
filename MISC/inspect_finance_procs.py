import re

with open("DAL_BKP_08042026", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

for proc in ["sp_update_transaction", "sp_update_account_receivable", "sp_update_account_payable", "sp_update_monthly_collection", "sp_update_monthly_payment"]:
    m = re.search(r'CREATE (?:OR REPLACE )?PROCEDURE [^\(]*?' + proc + r'\s*\((.*?)\)\s+LANGUAGE [^\n]+\s+AS \$\$([\s\S]*?)\$\$;', text, re.IGNORECASE)
    if m:
        body = m.group(2)
        print(f"\n*** {proc} ***")
        for l in body.split("\n")[:25]:
            if l.strip():
                print(" ", l.strip())

