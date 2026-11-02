from connector import OdooClient
client = OdooClient()
client.authenticate()

# Let's inspect an invoice's related fields
inv = client.search_read("account.move", domain=[("id", "=", 1959358)], fields=["id", "name", "invoice_user_id", "team_id", "stock_move_id", "partner_shipping_id", "invoice_origin"])
print("Invoice info:", inv)

# Let's check if invoice_origin has a sale order (e.g. S0001 or similar)
origin = inv[0].get("invoice_origin")
if origin:
    print("Origin:", origin)
    so = client.search_read("sale.order", domain=[("name", "=", origin)], fields=["id", "name", "warehouse_id", "user_id"])
    print("Sale order:", so)

