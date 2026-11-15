import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

sos = client.search_read(
    model="sale.order",
    domain=[],
    fields=["warehouse_id"],
    limit=100
)
wh_counts = {}
for s in sos:
    wh = s.get("warehouse_id")
    wh_name = wh[1] if wh else "None"
    wh_counts[wh_name] = wh_counts.get(wh_name, 0) + 1

print("Sale Order Warehouse Distribution (sample 100):", wh_counts)

