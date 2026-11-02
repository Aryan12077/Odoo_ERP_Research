from connector import OdooClient
from pipelines.base import get_m2o_id, get_m2o_name, safe_num
client = OdooClient()
client.authenticate()

# 1. Sales Data Enrichment Test
print("Testing Sales Data Enrichment...")
lines = client.search_read(
    "account.move.line",
    domain=[("parent_state", "=", "posted"), ("move_type", "in", ["out_invoice", "out_refund"]), ("display_type", "in", ["product", False])],
    fields=["id", "move_id", "move_name", "date", "partner_id", "product_id", "quantity", "price_unit", "price_subtotal", "price_total", "company_id", "currency_id", "move_type"],
    limit=10,
    order="date desc, id desc"
)

move_ids = list({get_m2o_id(l.get("move_id")) for l in lines if get_m2o_id(l.get("move_id"))})
move_map = {}
if move_ids:
    moves = client.search_read("account.move", domain=[("id", "in", move_ids)], fields=["id", "name", "invoice_user_id", "invoice_origin"])
    move_map = {m["id"]: m for m in moves}

for l in lines[:3]:
    m_info = move_map.get(get_m2o_id(l.get("move_id")), {})
    exec_id = get_m2o_id(m_info.get("invoice_user_id"))
    exec_name = get_m2o_name(m_info.get("invoice_user_id"), "NA")
    inv_num = l.get("move_name") or get_m2o_name(l.get("move_id"), "NA")
    print(f"  Sales Line {l['id']}: Invoice={inv_num}, Exec={exec_id}:{exec_name}")

# 2. Purchase Data Enrichment Test
print("\nTesting Purchase Data Enrichment...")
p_lines = client.search_read(
    "purchase.order.line",
    domain=[("state", "in", ["purchase", "done"])],
    fields=["id", "order_id", "partner_id", "product_id", "product_qty", "qty_received", "price_unit", "price_subtotal", "date_planned", "company_id", "state"],
    limit=10,
    order="id desc"
)

order_ids = list({get_m2o_id(l.get("order_id")) for l in p_lines if get_m2o_id(l.get("order_id"))})
order_map = {}
if order_ids:
    orders = client.search_read("purchase.order", domain=[("id", "in", order_ids)], fields=["id", "name", "picking_type_id", "picking_ids", "invoice_ids"])
    order_map = {o["id"]: o for o in orders}

for l in p_lines[:3]:
    o_info = order_map.get(get_m2o_id(l.get("order_id")), {})
    pt = get_m2o_name(o_info.get("picking_type_id"), "NA")
    wh = pt.split(":")[0].strip() if ":" in pt else pt
    picks = o_info.get("picking_ids", [])
    bills = o_info.get("invoice_ids", [])
    print(f"  PO Line {l['id']}: PO={get_m2o_name(l.get('order_id'))}, WH={wh}, PickingCount={len(picks)}, BillCount={len(bills)}")

# 3. Product Category Hierarchy Test
print("\nTesting Product Category Hierarchy...")
cats = client.search_read("product.category", fields=["id", "complete_name"])
cat_map = {c["id"]: c["complete_name"] for c in cats}

pts = client.search_read("product.template", domain=[("active", "=", True)], fields=["id", "name", "categ_id"], limit=5)
for p in pts:
    c_id = get_m2o_id(p.get("categ_id"))
    full_path = cat_map.get(c_id, "")
    parts = [x.strip() for x in full_path.split("/") if x.strip()]
    g1 = parts[0] if len(parts) > 0 else "General"
    g2 = parts[1] if len(parts) > 1 else "NA"
    g3 = parts[2] if len(parts) > 2 else "NA"
    print(f"  Product {p['name'][:30]}: Group={g1}, Sub={g2}, SubSub={g3}")

