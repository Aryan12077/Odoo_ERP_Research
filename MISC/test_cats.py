from connector import OdooClient
client = OdooClient()
client.authenticate()

# Test product categories
cats = client.search_read("product.category", fields=["id", "name", "complete_name", "parent_id"], limit=10)
print("Product Categories:")
for c in cats:
    print(c)

