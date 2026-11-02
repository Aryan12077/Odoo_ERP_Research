from connector import OdooClient
client = OdooClient()
client.authenticate()

quants = client.search_read("stock.quant", domain=[("location_id.usage", "=", "internal"), ("quantity", ">", 0)], fields=["id", "product_id", "location_id", "warehouse_id", "company_id", "quantity", "in_date"], limit=3)
for q in quants:
    print(q)

