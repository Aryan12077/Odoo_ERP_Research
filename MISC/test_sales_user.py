from connector import OdooClient
client = OdooClient()
client.authenticate()

# Fetch 2 move lines
lines = client.search_read("account.move.line", domain=[("move_type", "=", "out_invoice"), ("parent_state", "=", "posted"), ("display_type", "=", "product")], fields=["id", "move_id", "move_name", "date", "partner_id", "product_id", "quantity", "price_unit", "price_subtotal", "price_total", "company_id", "currency_id", "move_type"], limit=5)

move_ids = list({l["move_id"][0] for l in lines if l.get("move_id")})
moves = client.search_read("account.move", domain=[("id", "in", move_ids)], fields=["id", "name", "invoice_user_id", "team_id", "invoice_date"])
move_map = {m["id"]: m for m in moves}

for l in lines:
    m_info = move_map.get(l["move_id"][0], {})
    user_info = m_info.get("invoice_user_id")
    print(f"Line {l['id']}: Move {l['move_id'][1]} -> User: {user_info}")

