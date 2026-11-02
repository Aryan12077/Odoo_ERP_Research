import xmlrpc.client
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USERNAME')
password = os.getenv('ODOO_SECRET')

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
print("version: ", common.version())

uid = common.authenticate(
    db,
    username,
    password,
    {}
)

print("UID:", uid, type(uid))

if uid:
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    # Example: Fetching the list of users
    users = models.execute_kw(db, uid, password, 'res.users', 'search_read', [[]], {'fields': ['id', 'name', 'login']})
    print("Users:", users)

    partners = models.execute_kw(db, uid, password, 'res.partner', 'search_read', [[]], {'fields': ['id', 'name', 'email']})
    print("Partners:", partners)

    partners_count = models.execute_kw(db, uid, password, 'res.partner', 'search_count', [[]])
    print("Total Partners Count:", partners_count)

    partner_read = models.execute_kw(db, uid, password, 'res.partner', 'read', [[1]], {'fields': ['id', 'name', 'email']})
    print("Partner Read:", partner_read)

else:
    print("Authentication failed. Please check your credentials.")    