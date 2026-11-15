import sys, os, time
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

lines = client.search_read(
    model="account.move.line",
    domain=[
        ("parent_state", "=", "posted"),
        ("move_type", "in", ["out_invoice", "out_refund"]),
        ("display_type", "in", ["product", False]),
    ],
    fields=["id", "product_id"],
    limit=5000,
    order="date desc, id desc"
)
product_ids = list({l["product_id"][0] for l in lines if l.get("product_id")})
print(f"Distinct product_ids: {len(product_ids)}")

t0 = time.time()
costs_map = {}
for i in range(0, len(product_ids), 300):
    chunk = product_ids[i:i + 300]
    print(f"Querying chunk {i} to {i+len(chunk)}...")
    prods = client.search_read(
        model="product.product",
        domain=[("id", "in", chunk)],
        fields=["id", "standard_price"]
    )
    for p in prods:
        costs_map[p["id"]] = p.get("standard_price", 0.0)

print(f"Done querying {len(costs_map)} product costs in {time.time() - t0:.2f}s.")
