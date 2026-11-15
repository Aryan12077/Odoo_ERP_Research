import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
uid = client.authenticate()
print(f"Connected to Odoo! UID: {uid}")

pt_fields = client.execute_kw("product.template", "fields_get", [], {"attributes": ["string", "type"]})
custom_pt = {k: v for k, v in pt_fields.items() if k.startswith('x_') or any(w in k.lower() for w in ['brand', 'oem', 'make', 'size', 'style', 'sub', 'group', 'sbu', 'abc', 'ved', 'warranty', 'discount'])}
print(f"\nProduct Template matching fields ({len(custom_pt)}):")
for k, v in sorted(custom_pt.items()):
    print(f"  {k:30}: {v.get('type'):12} | {v.get('string')}")

rp_fields = client.execute_kw("res.partner", "fields_get", [], {"attributes": ["string", "type"]})
custom_rp = {k: v for k, v in rp_fields.items() if k.startswith('x_') or any(w in k.lower() for w in ['region', 'zone', 'area', 'category', 'industry', 'limit', 'credit', 'type'])}
print(f"\nRes Partner matching fields ({len(custom_rp)}):")
for k, v in sorted(custom_rp.items()):
    print(f"  {k:30}: {v.get('type'):12} | {v.get('string')}")
