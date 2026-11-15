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
fields = ["id", "date"]

t0 = time.time()
print("Testing order='id desc'...")
lines_id = client.search_read("account.move.line", base_domain, fields, limit=5000, order="id desc")
print(f"order='id desc' took {time.time() - t0:.2f}s for 5000 rows.")

t1 = time.time()
print("Testing order='date desc, id desc'...")
try:
    lines_date = client.search_read("account.move.line", base_domain, fields, limit=5000, order="date desc, id desc")
    print(f"order='date desc, id desc' took {time.time() - t1:.2f}s.")
except Exception as e:
    print(f"order='date desc, id desc' FAILED in {time.time() - t1:.2f}s: {e}")

