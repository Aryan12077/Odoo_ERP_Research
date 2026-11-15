import sys, os, time
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

base_domain = [
    ("parent_state", "=", "posted"),
    ("move_type", "in", ["out_invoice", "out_refund"]),
    ("display_type", "in", ["product", False]),
]

fields_with_move_name = [
    "id", "move_id", "move_name", "date", "partner_id", "product_id",
    "quantity", "price_unit", "price_subtotal", "price_total",
    "company_id", "currency_id", "currency_rate", "move_type"
]

fields_without_move_name = [
    "id", "move_id", "date", "partner_id", "product_id",
    "quantity", "price_unit", "price_subtotal", "price_total",
    "company_id", "currency_id", "currency_rate", "move_type"
]

t0 = time.time()
print("Testing without move_name...")
l1 = client.search_read("account.move.line", base_domain, fields_without_move_name, limit=5000, order="id desc")
print(f"Without move_name took {time.time() - t0:.2f}s for {len(l1)} rows.")

t1 = time.time()
print("Testing with move_name...")
try:
    l2 = client.search_read("account.move.line", base_domain, fields_with_move_name, limit=5000, order="id desc")
    print(f"With move_name took {time.time() - t1:.2f}s.")
except Exception as e:
    print(f"With move_name FAILED in {time.time() - t1:.2f}s: {e}")

