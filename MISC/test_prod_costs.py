import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

# Fetch 500 lines to see distinct products
lines = client.search_read(
    model="account.move.line",
    domain=[("parent_state", "=", "posted"), ("move_type", "in", ["out_invoice", "out_refund"]), ("display_type", "in", ["product", False])],
    fields=["product_id"],
    limit=500
)
p_ids = list({l["product_id"][0] for l in lines if l.get("product_id")})
print(f"500 lines have {len(p_ids)} distinct products.")

prods = client.search_read("product.product", [("id", "in", p_ids[:100])], ["id", "standard_price"])
print(f"Fetched costs for {len(prods)} products successfully! Sample: {prods[0]}")

