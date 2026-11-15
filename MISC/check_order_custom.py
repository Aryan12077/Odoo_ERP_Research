import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
uid = client.authenticate()

for model in ['sale.order', 'purchase.order', 'account.move']:
    fields = client.execute_kw(model, "fields_get", [], {"attributes": ["string", "type"]})
    custom = {k: v for k, v in fields.items() if k.startswith('x_')}
    print(f"\n{model} custom fields ({len(custom)}):")
    for k, v in sorted(custom.items()):
        print(f"  {k:30}: {v.get('type'):12} | {v.get('string')}")

