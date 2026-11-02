"""
Script 1: Odoo Tables Catalog Extractor

Fetches all tables / models present in the Odoo database.
Output format:
  table_id, table_name, table_description

Saves output to 'odoo_tables.csv' and optionally loads into PostgreSQL.
"""

import csv
import sys
import time
from connector import OdooClient


def fetch_all_odoo_tables():
    print("=" * 70)
    print("FETCHING ALL TABLES / MODELS FROM ODOO DATABASE")
    print("=" * 70)

    client = OdooClient()
    try:
        uid = client.authenticate()
        print(f"Connected to Odoo successfully (UID: {uid})\n")
    except Exception as e:
        print(f"[ERROR] Failed to connect to Odoo: {e}")
        sys.exit(1)

    tables = []

    # Attempt 1: Query ir.model directly (works if user has Administration rights)
    try:
        print("Checking if 'ir.model' is accessible directly...")
        models_data = client.search_read(
            model="ir.model",
            fields=["id", "model", "name"],
            limit=5000,
            order="id asc"
        )
        print(f"Successfully fetched {len(models_data)} models directly from ir.model!")
        for m in models_data:
            tables.append({
                "table_id": m["id"],
                "table_name": m["model"].replace(".", "_"),
                "table_description": m.get("name") or m["model"]
            })
    except Exception as e:
        print(f"Direct 'ir.model' query restricted for this user role ({e}).")
        print("Switching to active system model discovery & catalog scan...\n")

        # Attempt 2: Comprehensive catalog of Odoo modules and models
        known_models = [
            # Base & Organizations
            ("res.company", "Company Master"),
            ("res.users", "User Master"),
            ("res.partner", "Contact / Partner Master"),
            ("res.partner.category", "Partner Tags"),
            ("res.partner.bank", "Partner Bank Accounts"),
            ("res.currency", "Currency Master"),
            ("res.currency.rate", "Currency Exchange Rates"),
            ("res.country", "Country Master"),
            ("res.country.state", "State / Province Master"),
            ("res.groups", "Access Groups"),
            ("res.lang", "Languages"),

            # Product Master
            ("product.template", "Product Template Master"),
            ("product.product", "Product Variant Master"),
            ("product.category", "Product Category"),
            ("product.pricelist", "Pricelist Master"),
            ("product.pricelist.item", "Pricelist Items"),
            ("product.supplierinfo", "Vendor Pricelists / Lead Times"),
            ("product.packaging", "Product Packaging"),
            ("uom.uom", "Unit of Measure"),
            ("uom.category", "UOM Category"),

            # Sales
            ("sale.order", "Sales Order Header"),
            ("sale.order.line", "Sales Order Line Items"),
            ("sale.order.option", "Optional Products Line"),
            ("crm.lead", "Lead / Opportunity"),
            ("crm.team", "Sales Team"),
            ("crm.stage", "CRM Stages"),

            # Purchase
            ("purchase.order", "Purchase Order Header"),
            ("purchase.order.line", "Purchase Order Line Items"),
            ("purchase.requisition", "Purchase Agreement / Tender"),

            # Inventory / Stock
            ("stock.warehouse", "Warehouse Master"),
            ("stock.location", "Stock Storage Location"),
            ("stock.location.route", "Stock Routes"),
            ("stock.quant", "Current On-Hand Stock (Quants)"),
            ("stock.move", "Stock Movement Header"),
            ("stock.move.line", "Stock Movement Details"),
            ("stock.picking", "Stock Delivery / Receipt Transfers"),
            ("stock.picking.type", "Operation Types (Receipts, Deliveries)"),
            ("stock.lot", "Serial Numbers / Lots"),
            ("stock.valuation.layer", "Stock Valuation Accounting Layer"),
            ("stock.warehouse.orderpoint", "Reordering Rules"),
            ("stock.scrap", "Scrapped Stock"),
            ("stock.package.level", "Package Levels"),

            # Accounting & Finance
            ("account.move", "Journal Entries / Customer Invoices / Vendor Bills"),
            ("account.move.line", "Journal Items (General Ledger Lines)"),
            ("account.account", "Chart of Accounts (G/L Accounts)"),
            ("account.account.tag", "Account Tags"),
            ("account.group", "Account Groups"),
            ("account.journal", "Accounting Journals"),
            ("account.tax", "Taxes Master"),
            ("account.tax.group", "Tax Groups"),
            ("account.payment", "Customer Receipts & Vendor Payments"),
            ("account.payment.term", "Payment Terms"),
            ("account.fiscal.year", "Fiscal Years"),
            ("account.fiscal.position", "Fiscal Positions"),
            ("account.bank.statement", "Bank Statements"),
            ("account.bank.statement.line", "Bank Statement Lines"),
            ("account.analytic.account", "Analytic Cost Centers"),
            ("account.analytic.line", "Analytic Entries"),

            # Manufacturing (MRP)
            ("mrp.production", "Manufacturing Production Orders"),
            ("mrp.bom", "Bill of Materials (BOM Header)"),
            ("mrp.bom.line", "BOM Component Lines"),
            ("mrp.workorder", "Manufacturing Work Orders"),
            ("mrp.routing.workcenter", "Workcenter Routings"),

            # Maintenance & Quality
            ("maintenance.equipment", "Maintenance Equipment"),
            ("maintenance.request", "Maintenance Requests"),
            ("quality.check", "Quality Checks"),
            ("quality.point", "Quality Control Points"),

            # System & UI Menus
            ("ir.ui.menu", "System Navigation Menus"),
            ("ir.module.module", "Installed System Modules"),
            ("mail.activity", "Activities & Tasks"),
            ("mail.message", "Messages & Discussions"),
            ("mail.followers", "Document Followers")
        ]

        print(f"Verifying access to {len(known_models)} standard and custom models...")
        checked_idx = 1
        for model_name, desc in known_models:
            try:
                # Test if model exists and fields can be retrieved
                client.execute_kw(model_name, "fields_get", args=[["id"]])
                tables.append({
                    "table_id": checked_idx,
                    "table_name": model_name.replace(".", "_"),
                    "table_description": desc
                })
                checked_idx += 1
            except Exception:
                # Model is not installed on this instance; skip safely
                pass

    print(f"\nDiscovered {len(tables)} verified active tables in this Odoo database.\n")

    # Save to CSV
    csv_file = "odoo_tables.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["table_id", "table_name", "table_description"])
        writer.writeheader()
        writer.writerows(tables)

    print(f"--> Saved to: {csv_file}")

    # Display preview table
    print("\nSample Preview (First 15 Tables):")
    print(f"{'Table ID':<10} | {'Table Name (Postgres)':<35} | {'Description'}")
    print("-" * 80)
    for t in tables[:15]:
        print(f"{t['table_id']:<10} | {t['table_name']:<35} | {t['table_description']}")

    if len(tables) > 15:
        print(f"... and {len(tables) - 15} more tables in {csv_file}")

    print("=" * 70)


if __name__ == "__main__":
    fetch_all_odoo_tables()

