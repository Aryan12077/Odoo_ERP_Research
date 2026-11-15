import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

whs = client.search_read("stock.warehouse", [], ["id", "name", "code", "company_id", "partner_id"])
print(f"Warehouses ({len(whs)}):")
for w in whs:
    print(w)

locs = client.search_read("stock.location", [("usage", "=", "internal")], ["id", "name", "complete_name", "usage", "warehouse_id", "company_id"], limit=10)
print(f"\nInternal Locations sample ({len(locs)}):")
for l in locs:
    print(l)

