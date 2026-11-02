from connector import OdooClient
client = OdooClient()
client.authenticate()

po = client.search_read("purchase.order", domain=[("id", "=", 4098)], fields=["id", "name", "picking_ids", "invoice_ids", "picking_type_id"])
print("PO info:", po)

if po[0].get("picking_ids"):
    picks = client.search_read("stock.picking", domain=[("id", "in", po[0]["picking_ids"])], fields=["id", "name", "date_done", "state"])
    print("Pickings (GRNs):", picks)

if po[0].get("invoice_ids"):
    invs = client.search_read("account.move", domain=[("id", "in", po[0]["invoice_ids"])], fields=["id", "name", "invoice_date", "state"])
    print("Invoices (Vendor Bills):", invs)

