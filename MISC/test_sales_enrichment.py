import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

# Test retrieving 20 lines with sale_line_ids
lines = client.search_read(
    model="account.move.line",
    domain=[("parent_state", "=", "posted"), ("move_type", "in", ["out_invoice", "out_refund"]), ("display_type", "in", ["product", False])],
    fields=["id", "move_id", "product_id", "quantity", "price_subtotal", "sale_line_ids"],
    limit=20
)

all_sol_ids = set()
for l in lines:
    for sid in l.get("sale_line_ids", []):
        all_sol_ids.add(sid)

print(f"Lines: {len(lines)}, distinct sol_ids: {len(all_sol_ids)}")

if all_sol_ids:
    sols = client.search_read("sale.order.line", [("id", "in", list(all_sol_ids))], ["id", "order_id"])
    so_ids = list({s["order_id"][0] for s in sols if s.get("order_id")})
    sos = client.search_read("sale.order", [("id", "in", so_ids)], ["id", "warehouse_id", "user_id"])
    so_map = {s["id"]: s for s in sos}
    sol_map = {s["id"]: so_map.get(s["order_id"][0]) for s in sols if s.get("order_id")}
    print(f"Sample mapped warehouse: {next(iter(so_map.values()))}")

