import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

# Check sample invoice lines
lines = client.search_read(
    model="account.move.line",
    domain=[("parent_state", "=", "posted"), ("move_type", "=", "out_invoice"), ("product_id", "!=", False)],
    fields=["id", "name", "product_id", "sale_line_ids"],
    limit=5
)
print("Sample invoice lines sale_line_ids:")
for l in lines:
    print(l)

