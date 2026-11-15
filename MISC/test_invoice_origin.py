import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

moves = client.search_read(
    model="account.move",
    domain=[("move_type", "=", "out_invoice"), ("state", "=", "posted")],
    fields=["id", "name", "invoice_origin", "invoice_user_id"],
    limit=10
)
print("Sample account.move:")
for m in moves:
    print(m)

