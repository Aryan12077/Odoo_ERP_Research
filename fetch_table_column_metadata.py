"""
Script 2: Odoo Table Column Metadata Extractor

Fetches full column/field metadata for all models useful to the codebase/data warehouse:
  table_name, table_description, column_name, column_description, column_datatype, column_length

Saves output to 'odoo_table_column_metadata.csv'.
"""

import csv
import sys
import time
from connector import OdooClient


USEFUL_MODELS = [
    # Masters
    ("res.company", "res_company", "Company Master"),
    ("res.partner", "res_partner", "Customer & Vendor Master (Contacts)"),
    ("res.users", "res_users", "User & Sales Executive Master"),
    ("res.currency", "res_currency", "Currency Master"),
    ("res.country", "res_country", "Country Master"),
    ("res.country.state", "res_country_state", "State / Province Master"),
    ("product.template", "product_template", "Product Master"),
    ("product.product", "product_product", "Product Variant Master"),
    ("product.category", "product_category", "Product Category Hierarchy"),
    ("uom.uom", "uom_uom", "Unit of Measure"),
    ("account.account", "account_account", "Chart of Accounts (G/L Accounts)"),
    ("account.journal", "account_journal", "Accounting Journals"),

    # Sales
    ("sale.order", "sale_order", "Sales Orders Header"),
    ("sale.order.line", "sale_order_line", "Sales Order Line Items"),

    # Purchase
    ("purchase.order", "purchase_order", "Purchase Orders Header"),
    ("purchase.order.line", "purchase_order_line", "Purchase Order Line Items"),

    # Inventory
    ("stock.warehouse", "stock_warehouse", "Warehouse Master"),
    ("stock.location", "stock_location", "Storage Location Hierarchy"),
    ("stock.quant", "stock_quant", "Current On-Hand Stock (Quants)"),
    ("stock.move", "stock_move", "Stock Movement Records"),
    ("stock.move.line", "stock_move_line", "Stock Movement Line Details"),
    ("stock.picking", "stock_picking", "Delivery Orders & Receipts (Transfers)"),

    # Finance
    ("account.move", "account_move", "Invoices, Bills & Journal Entries"),
    ("account.move.line", "account_move_line", "General Ledger Items (AR, AP, GL)"),
    ("account.payment", "account_payment", "Customer Receipts & Vendor Payments"),
]


def fetch_column_metadata():
    print("=" * 70)
    print("FETCHING COLUMN METADATA FOR CORE ERP TABLES")
    print("=" * 70)

    client = OdooClient()
    try:
        uid = client.authenticate()
        print(f"Connected to Odoo successfully (UID: {uid})\n")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Odoo: {e}")
        sys.exit(1)

    all_columns = []
    total_start = time.time()

    print(f"Extracting field schemas for {len(USEFUL_MODELS)} core tables...")
    print("-" * 70)

    for odoo_model, pg_table, desc in USEFUL_MODELS:
        try:
            start_m = time.time()
            fields_meta = client.execute_kw(
                model=odoo_model,
                method="fields_get",
                args=[]
            )
            elapsed = round(time.time() - start_m, 2)
            col_count = len(fields_meta)

            for col_name, f_data in sorted(fields_meta.items()):
                datatype = f_data.get("type") or "unknown"

                # Column length / size or target relational model
                length = ""
                if f_data.get("size"):
                    length = str(f_data.get("size"))
                elif f_data.get("relation"):
                    length = f"Ref({f_data.get('relation')})"
                elif datatype in ("integer", "bigint"):
                    length = "4" if datatype == "integer" else "8"
                elif datatype in ("float", "monetary"):
                    length = "8"
                elif datatype in ("date", "datetime"):
                    length = "timestamp" if datatype == "datetime" else "date"

                all_columns.append({
                    "table_name": pg_table,
                    "table_description": desc,
                    "column_name": col_name,
                    "column_description": f_data.get("string") or col_name,
                    "column_datatype": datatype,
                    "column_length": length
                })

            print(f"--> {pg_table:<22} ({odoo_model:<20}): {col_count:>4} columns in {elapsed}s")

        except Exception as e:
            print(f"--> {pg_table:<22} ({odoo_model:<20}): [SKIPPED] {e}")

    total_elapsed = round(time.time() - total_start, 2)
    print("-" * 70)
    print(f"Total Columns Extracted: {len(all_columns)} across {len(USEFUL_MODELS)} tables in {total_elapsed}s\n")

    # Save to CSV
    csv_file = "odoo_table_column_metadata.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "table_name",
            "table_description",
            "column_name",
            "column_description",
            "column_datatype",
            "column_length"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_columns)

    print(f"--> Saved metadata to CSV: {csv_file}")

    # Display sample preview
    print("\nSample Metadata Preview (First 10 Columns):")
    print(f"{'Table':<15} | {'Column':<22} | {'Type':<12} | {'Length/Ref':<18} | {'Description'}")
    print("-" * 90)
    for c in all_columns[:10]:
        print(f"{c['table_name']:<15} | {c['column_name']:<22} | {c['column_datatype']:<12} | {c['column_length']:<18} | {c['column_description']}")

    print(f"... and {len(all_columns) - 10} more column rows in {csv_file}")
    print("=" * 70)


if __name__ == "__main__":
    fetch_column_metadata()

