import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

sol = client.search_read(
    model="sale.order.line",
    domain=[("id", "in", [1772293, 1772294])],
    fields=["id", "order_id"]
)
print("Sale order lines:", sol)

so_id = sol[0]["order_id"][0]
so = client.search_read(
    model="sale.order",
    domain=[("id", "=", so_id)],
    fields=["id", "name", "warehouse_id", "user_id"]
)
print("Sale order:", so)

