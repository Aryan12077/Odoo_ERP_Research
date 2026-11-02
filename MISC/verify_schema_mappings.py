import os
import re
import csv
import importlib
import sys

# 1. Parse Table_references.sql
with open("Table_references.sql", "r", encoding="utf-8") as f:
    sql_text = f.read()

# Match CREATE TABLE "EVA_BI"."<table_name>" ( ... );
table_blocks = re.findall(r'CREATE TABLE "(?:EVA_BI|odoo_roshni)"\."([A-Za-z0-9_]+)"\s*\((.*?)\);', sql_text, re.DOTALL | re.IGNORECASE)

dwh_tables = {}
for tbl_name, cols_block in table_blocks:
    cols = []
    for line in cols_block.strip().split("\n"):
        line = line.strip().rstrip(",")
        if not line or line.startswith("--"):
            continue
        m = re.match(r'"?([A-Za-z0-9_ ]+)"?\s+([A-Za-z0-9_ ]+)', line)
        if m:
            cname = m.group(1).strip()
            ctype = m.group(2).strip()
            cols.append((cname, ctype))
    dwh_tables[tbl_name] = cols

print(f"Parsed {len(dwh_tables)} DWH tables from Table_references.sql")

# 2. Load Odoo table column metadata
odoo_meta = {}
if os.path.exists("odoo_table_column_metadata.csv"):
    with open("odoo_table_column_metadata.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tname = row["table_name"]
            cname = row["column_name"]
            if tname not in odoo_meta:
                odoo_meta[tname] = {}
            odoo_meta[tname][cname] = row

print(f"Loaded metadata for {len(odoo_meta)} Odoo models.")

# 3. Check each pipeline extractor
from pipelines.masters.company import CompanyMasterExtractor
from pipelines.masters.branch import BranchMasterExtractor
from pipelines.masters.currency import CurrencyMasterExtractor
from pipelines.masters.accounts import ChartOfAccountExtractor, AccountTypeExtractor
from pipelines.masters.customer import CustomerMasterExtractor
from pipelines.masters.supplier import SupplierMasterExtractor
from pipelines.masters.product import ProductMasterExtractor

from pipelines.sales.sales_data import SalesDataExtractor
from pipelines.sales.monthly_sale import MonthlySaleExtractor

from pipelines.purchase.purchase_data import PurchaseDataExtractor
from pipelines.purchase.monthly_purchase import MonthlyPurchaseExtractor

from pipelines.inventory.inventory_ageing import InventoryAgeingExtractor

from pipelines.finance.transaction import TransactionExtractor
from pipelines.finance.account_receivable import AccountReceivableExtractor
from pipelines.finance.account_payable import AccountPayableExtractor
from pipelines.finance.monthly_collection import MonthlyCollectionExtractor
from pipelines.finance.monthly_payment import MonthlyPaymentExtractor

extractors = [
    # Masters
    ("COMPANY_MASTER", CompanyMasterExtractor),
    ("BRANCH_MASTER", BranchMasterExtractor),
    ("CURRENCY_MASTER", CurrencyMasterExtractor),
    ("CHART_OF_ACCOUNT", ChartOfAccountExtractor),
    ("ACCOUNT_TYPE", AccountTypeExtractor),
    ("CUSTOMER_MASTER", CustomerMasterExtractor),
    ("SUPPLIER_MASTER", SupplierMasterExtractor),
    ("PRODUCT_MASTER", ProductMasterExtractor),
    # Sales
    ("SALES_DATA", SalesDataExtractor),
    ("MONTHLY_SALE", MonthlySaleExtractor),
    # Purchase
    ("PURCHASE_DATA", PurchaseDataExtractor),
    ("MONTHLY_PURCHASE", MonthlyPurchaseExtractor),
    # Inventory
    ("INVENTORY_AGEING", InventoryAgeingExtractor),
    # Finance
    ("TRANSACTION", TransactionExtractor),
    ("ACCOUNT_RECEIVABLE", AccountReceivableExtractor),
    ("ACCOUNT_PAYABLE", AccountPayableExtractor),
    ("MONTHLY_COLLECTION", MonthlyCollectionExtractor),
    ("MONTHLY_PAYMENT", MonthlyPaymentExtractor),
]

print("\n" + "="*80)
print("AUDIT: DWH TABLE COLUMNS VS EXTRACTOR DICT KEYS")
print("="*80)

for tbl_name, ext_cls in extractors:
    dwh_cols = [c[0] for c in dwh_tables.get(tbl_name, [])]
    if not dwh_cols:
        print(f"[!] Warning: Table {tbl_name} not found in Table_references.sql")
        continue

    # Inspect code of extract() method to see returned dictionary keys
    import inspect
    lines, _ = inspect.getsourcelines(ext_cls.extract)
    code = "".join(lines)
    
    # Extract keys inside rows.append({ ... }) or dict literal
    dict_keys = re.findall(r'["\']([A-Za-z0-9_ ]+)["\']\s*:', code)
    # Deduplicate while preserving order
    unique_keys = []
    for k in dict_keys:
        if k not in unique_keys and k in [c[0] for c in dwh_tables.get(tbl_name, [])]:
            unique_keys.append(k)

    missing_in_extractor = set(dwh_cols) - set(unique_keys)
    extra_in_extractor = set(unique_keys) - set(dwh_cols)

    # Let's check exact match
    print(f"\nTable: {tbl_name} (Target cols: {len(dwh_cols)}, Extractor mapped: {len(unique_keys)})")
    if missing_in_extractor:
        print(f"  [-] Columns in DWH but missing in Extractor: {missing_in_extractor}")
    if extra_in_extractor:
        print(f"  [+] Columns in Extractor but NOT in DWH: {extra_in_extractor}")
    if not missing_in_extractor and not extra_in_extractor:
        print(f"  [OK] 100% exact column match! ({len(unique_keys)}/{len(dwh_cols)} columns)")

