import sys, os
sys.path.insert(0, os.path.abspath('.'))
from connector import OdooClient

client = OdooClient()
client.authenticate()

comps = client.search_read("res.company", [], ["id", "name", "fiscalyear_last_day", "fiscalyear_last_month"])
print("Company Fiscal Settings:", comps)

