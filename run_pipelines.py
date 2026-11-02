"""
Master Pipeline Runner / Orchestrator for Odoo to EVA_BI Data Warehouse.

Usage:
  # Test extraction for a specific domain (dry run without DB load)
  python run_pipeline.py --domain sales
  python run_pipeline.py --domain purchase
  python run_pipeline.py --domain inventory
  python run_pipeline.py --domain finance
  python run_pipeline.py --domain masters

  # Run and load into target PostgreSQL DWH (when TARGET_DB_* is set in .env)
  python run_pipeline.py --domain sales --load

  # Run a specific extractor
  python run_pipeline.py --extractor sales_data
  python run_pipeline.py --extractor customer_master
"""

import argparse
import json
import sys
import time
from datetime import datetime

from connector import OdooClient
from db_loader import DWHLoader

# Import extractors
from pipelines.masters.company import CompanyMasterExtractor
from pipelines.masters.branch import BranchMasterExtractor
from pipelines.masters.customer import CustomerMasterExtractor
from pipelines.masters.supplier import SupplierMasterExtractor
from pipelines.masters.product import ProductMasterExtractor
from pipelines.masters.currency import CurrencyMasterExtractor
from pipelines.masters.accounts import ChartOfAccountExtractor, AccountTypeExtractor

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


REGISTRY = {
    # Masters
    "company_master": CompanyMasterExtractor,
    "branch_master": BranchMasterExtractor,
    "customer_master": CustomerMasterExtractor,
    "supplier_master": SupplierMasterExtractor,
    "product_master": ProductMasterExtractor,
    "currency_master": CurrencyMasterExtractor,
    "chart_of_account": ChartOfAccountExtractor,
    "account_type": AccountTypeExtractor,

    # Sales
    "sales_data": SalesDataExtractor,
    "monthly_sale": MonthlySaleExtractor,

    # Purchase
    "purchase_data": PurchaseDataExtractor,
    "monthly_purchase": MonthlyPurchaseExtractor,

    # Inventory
    "inventory_ageing": InventoryAgeingExtractor,

    # Finance
    "transaction": TransactionExtractor,
    "account_receivable": AccountReceivableExtractor,
    "account_payable": AccountPayableExtractor,
    "monthly_collection": MonthlyCollectionExtractor,
    "monthly_payment": MonthlyPaymentExtractor,
}

DOMAINS = {
    "masters": [
        "company_master",
        "branch_master",
        "currency_master",
        "account_type",
        "chart_of_account",
        "customer_master",
        "supplier_master",
        "product_master",
    ],
    "sales": [
        "sales_data",
        "monthly_sale",
    ],
    "purchase": [
        "purchase_data",
        "monthly_purchase",
    ],
    "inventory": [
        "inventory_ageing",
    ],
    "finance": [
        "transaction",
        "account_receivable",
        "account_payable",
        "monthly_collection",
        "monthly_payment",
    ],
}


def main():
    parser = argparse.ArgumentParser(description="Odoo ETL Pipeline Runner")
    parser.add_argument(
        "--domain",
        choices=["all", "masters", "sales", "purchase", "inventory", "finance"],
        help="Run all extractors for a specific domain"
    )
    parser.add_argument(
        "--extractor",
        choices=list(REGISTRY.keys()),
        help="Run a specific extractor by name"
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Load extracted records into target PostgreSQL database (requires TARGET_DB in .env)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Batch limit for records to extract"
    )

    args = parser.parse_args()

    if not args.domain and not args.extractor:
        parser.print_help()
        sys.exit(1)

    print("=" * 70)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Odoo Data Pipeline Initiated")
    print(f"Mode: {'EXTRACT & LOAD' if args.load else 'EXTRACT ONLY (Dry Run)'}")
    print("=" * 70)

    # 1. Authenticate with Odoo
    print("\nConnecting to Odoo...")
    client = OdooClient()
    try:
        uid = client.authenticate()
        print(f"Odoo Connected Successfully! UID: {uid}")
    except Exception as e:
        print(f"Failed to authenticate with Odoo: {e}")
        sys.exit(1)

    # 2. Setup DWH Loader if --load requested
    loader = None
    if args.load:
        print("\nConnecting to Target PostgreSQL DWH...")
        try:
            loader = DWHLoader()
            test_res = loader.test_connection()
            if not test_res.get("connected"):
                print(f"Target DB Connection Error: {test_res.get('error')}")
                sys.exit(1)
            print(f"Target DB Connected: {test_res.get('version')[:50]}...")
            print(f"Schema '{test_res.get('schema')}' exists: {test_res.get('schema_exists')}")
        except Exception as e:
            print(f"Failed to initialize DWHLoader: {e}")
            sys.exit(1)

    # 3. Determine tasks to run
    tasks = []
    if args.extractor:
        tasks = [args.extractor]
    elif args.domain == "all":
        for d_list in DOMAINS.values():
            tasks.extend(d_list)
    else:
        tasks = DOMAINS[args.domain]

    # 4. Execute pipeline tasks
    print(f"\nRunning {len(tasks)} extractor task(s)...")
    print("-" * 70)

    results = []
    total_start = time.time()

    for task_name in tasks:
        extractor_cls = REGISTRY[task_name]
        try:
            # Check if constructor accepts batch_limit
            try:
                ext = extractor_cls(batch_limit=args.limit)
            except TypeError:
                ext = extractor_cls()

            print(f"--> Running: {task_name.upper()} (Table: {ext.target_table})...", end=" ", flush=True)
            res = ext.run(client, loader=loader)
            print(f"[{res.get('status')}] {res.get('extracted_count')} records in {res.get('extraction_duration_sec')}s")
            results.append(res)
        except Exception as e:
            print(f"[FAILED] Error: {e}")
            results.append({
                "table": task_name,
                "status": "FAILED",
                "error": str(e)
            })

    total_duration = round(time.time() - total_start, 2)

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    print(json.dumps(results, indent=2))
    print(f"\nTotal Pipeline Elapsed Time: {total_duration}s")
    print("=" * 70)


if __name__ == "__main__":
    main()

