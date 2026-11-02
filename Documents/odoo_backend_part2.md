# CHAPTER 6: POSTGRESQL DATABASE SCHEMA

## 6.1 How Python Models Map to Tables

Odoo's ORM automatically creates and maintains the PostgreSQL schema. You never write DDL manually.

### 6.1.1 The Naming Convention

```
Python class _name      →   PostgreSQL table name
─────────────────────────────────────────────────
'sale.order'            →   sale_order
'sale.order.line'       →   sale_order_line
'res.partner'           →   res_partner
'account.move'          →   account_move
'project.task'          →   project_task
'ir.model'              →   ir_model
```

The convention is: replace `.` with `_` and lowercase everything.

### 6.1.2 Field-to-Column Mapping

```
Python Field Type        →   PostgreSQL Column Type
──────────────────────────────────────────────────────
fields.Char              →   VARCHAR or TEXT
fields.Text              →   TEXT
fields.Html              →   TEXT
fields.Integer           →   INTEGER
fields.Float             →   NUMERIC (with precision)
fields.Monetary          →   NUMERIC(16, 2)
fields.Boolean           →   BOOLEAN
fields.Date              →   DATE
fields.Datetime          →   TIMESTAMP WITHOUT TIME ZONE
fields.Binary            →   BYTEA (or stored externally in ir.attachment)
fields.Selection         →   VARCHAR
fields.Many2one          →   INTEGER (foreign key)
fields.One2many          →   No column (virtual — FK is on the other table)
fields.Many2many         →   No column (junction table created separately)
fields.Char(translate=T) →   VARCHAR + entries in ir.translation
```

### 6.1.3 Standard Columns Added Automatically

Every `models.Model` (when `_log_access = True`, which is default) gets these columns:

```sql
-- Automatically added by ORM to every model
id              SERIAL PRIMARY KEY,
create_uid      INTEGER REFERENCES res_users(id),    -- Who created
create_date     TIMESTAMP WITHOUT TIME ZONE,          -- When created
write_uid       INTEGER REFERENCES res_users(id),     -- Who last modified
write_date      TIMESTAMP WITHOUT TIME ZONE,          -- When last modified
```

### 6.1.4 Inspecting the Actual SQL

```sql
-- See the real table structure for sale.order
\d sale_order

-- Or:
SELECT column_name, data_type, character_maximum_length, is_nullable
FROM information_schema.columns
WHERE table_name = 'sale_order'
ORDER BY ordinal_position;
```

Sample output for `sale_order`:
```
 column_name          | data_type                   | nullable
──────────────────────┼─────────────────────────────┼─────────
 id                   | integer                     | NO
 name                 | character varying           | YES
 date_order           | timestamp without time zone | YES
 partner_id           | integer                     | YES     ← Many2one FK
 amount_untaxed       | numeric                     | YES
 amount_tax           | numeric                     | YES
 amount_total         | numeric                     | YES
 state                | character varying           | YES
 company_id           | integer                     | YES
 user_id              | integer                     | YES
 warehouse_id         | integer                     | YES
 note                 | text                        | YES
 create_uid           | integer                     | YES
 create_date          | timestamp without time zone | YES
 write_uid            | integer                     | YES
 write_date           | timestamp without time zone | YES
```

## 6.2 Relational Fields in PostgreSQL

### 6.2.1 Many2one (Foreign Key)

```python
# Python:
class SaleOrder(models.Model):
    _name = 'sale.order'
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
```

```sql
-- PostgreSQL DDL generated:
ALTER TABLE sale_order 
  ADD COLUMN partner_id INTEGER;

ALTER TABLE sale_order 
  ADD CONSTRAINT sale_order_partner_id_fkey 
  FOREIGN KEY (partner_id) REFERENCES res_partner(id) 
  ON DELETE SET NULL;   -- or CASCADE/RESTRICT based on ondelete=

-- Index automatically created:
CREATE INDEX sale_order_partner_id_index ON sale_order(partner_id);
```

### 6.2.2 One2many (Inverse FK — No New Column)

```python
# Python:
class SaleOrder(models.Model):
    _name = 'sale.order'
    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines')

class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    order_id = fields.Many2one('sale.order', ondelete='cascade')
```

```sql
-- No column on sale_order for order_line!
-- The FK lives on sale_order_line:
ALTER TABLE sale_order_line ADD COLUMN order_id INTEGER;
ALTER TABLE sale_order_line 
  ADD CONSTRAINT sale_order_line_order_id_fkey
  FOREIGN KEY (order_id) REFERENCES sale_order(id) ON DELETE CASCADE;

-- ORM reads One2many as:
-- SELECT id FROM sale_order_line WHERE order_id = 42;
```

### 6.2.3 Many2many (Junction Table)

```python
# Python:
class ProjectTask(models.Model):
    _name = 'project.task'
    tag_ids = fields.Many2many(
        'project.tags',
        'project_task_tag_rel',   # junction table
        'task_id',                 # column for this model
        'tag_id',                  # column for the other model
    )
```

```sql
-- Junction table created:
CREATE TABLE project_task_tag_rel (
    task_id  INTEGER NOT NULL REFERENCES project_task(id) ON DELETE CASCADE,
    tag_id   INTEGER NOT NULL REFERENCES project_tags(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);

-- ORM reads Many2many as:
-- SELECT tag_id FROM project_task_tag_rel WHERE task_id = 15;

-- ORM writes Many2many as:
-- INSERT INTO project_task_tag_rel (task_id, tag_id) VALUES (15, 3);
-- DELETE FROM project_task_tag_rel WHERE task_id = 15 AND tag_id = 7;
```

## 6.3 Core System Tables

### 6.3.1 `res_partner` — The Universal Contact

```sql
-- Every person, company, customer, vendor, employee is a res.partner
SELECT id, name, email, phone, street, city, country_id, 
       is_company, company_id, active, customer_rank, supplier_rank
FROM res_partner
WHERE is_company = TRUE
LIMIT 5;

-- Hierarchy: a company can have multiple contacts
-- parent_id = NULL means top-level company
-- parent_id = (company id) means contact of that company
```

### 6.3.2 `res_users` — Authentication

```sql
-- res_users extends res_partner (via delegation inheritance)
-- Every user IS a partner
SELECT u.id, u.login, u.password, u.active, u.company_id,
       p.name, p.email
FROM res_users u
JOIN res_partner p ON u.partner_id = p.id;
```

### 6.3.3 `ir_model` and `ir_model_fields` — The Meta-Layer

```sql
-- List all installed models
SELECT id, name, model, state, transient
FROM ir_model
WHERE state = 'base'
LIMIT 10;

-- List all fields of sale.order
SELECT f.name, f.field_description, f.ttype, f.required, f.readonly, f.store
FROM ir_model_fields f
JOIN ir_model m ON f.model_id = m.id
WHERE m.model = 'sale.order'
ORDER BY f.name;
```

### 6.3.4 `ir_ui_view` — View Definitions

```sql
-- All views for sale.order
SELECT id, name, type, mode, priority, active
FROM ir_ui_view
WHERE model = 'sale.order'
ORDER BY priority;
```

### 6.3.5 `ir_rule` — Record Rules

```sql
-- All record rules
SELECT r.name, r.model_id, r.domain_force, r.perm_read, r.perm_write
FROM ir_rule r
JOIN ir_model m ON r.model_id = m.id
WHERE m.model = 'sale.order';
```

### 6.3.6 `ir_model_access` — ACL Table

```sql
-- Access rights per model per group
SELECT a.name, m.model, a.perm_read, a.perm_write, a.perm_create, a.perm_unlink
FROM ir_model_access a
JOIN ir_model m ON a.model_id = m.id
WHERE m.model = 'sale.order';
```

### 6.3.7 Important Tables Reference

| Table | Python Model | Purpose |
|---|---|---|
| `res_partner` | `res.partner` | All contacts |
| `res_users` | `res.users` | User accounts |
| `res_company` | `res.company` | Companies |
| `res_country` | `res.country` | Countries |
| `res_currency` | `res.currency` | Currencies |
| `ir_model` | `ir.model` | Model registry |
| `ir_model_fields` | `ir.model.fields` | Field definitions |
| `ir_ui_view` | `ir.ui.view` | View XML |
| `ir_ui_menu` | `ir.ui.menu` | Menu items |
| `ir_rule` | `ir.rule` | Record-level security |
| `ir_model_access` | `ir.model.access` | Model-level ACL |
| `ir_module_module` | `ir.module.module` | Installed modules |
| `ir_sequence` | `ir.sequence` | Auto-increment sequences |
| `ir_attachment` | `ir.attachment` | File attachments |
| `mail_message` | `mail.message` | Chatter messages |
| `sale_order` | `sale.order` | Sales orders |
| `sale_order_line` | `sale.order.line` | Sales order lines |
| `account_move` | `account.move` | Invoices/Journal entries |
| `stock_picking` | `stock.picking` | Delivery orders |

## 6.4 Exploring the Schema with Python

```python
# From a Python shell with Odoo environment loaded:

# List all models
models = env['ir.model'].search([('state', '=', 'base')])
for m in models:
    print(m.model, m.name)

# List all fields of a model
fields = env['ir.model.fields'].search([
    ('model_id.model', '=', 'sale.order')
])
for f in fields:
    print(f'{f.name:30} {f.ttype:15} {f.field_description}')

# Get table column info via SQL
env.cr.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = %s
    ORDER BY ordinal_position
""", ['sale_order'])
for row in env.cr.fetchall():
    print(row)

# Get all FK relationships for a table
env.cr.execute("""
    SELECT
        tc.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table,
        ccu.column_name AS foreign_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_name = %s
""", ['sale_order'])
for row in env.cr.fetchall():
    print(row)
```

## 6.5 Chapter Summary

- `_name = 'sale.order'` → `CREATE TABLE sale_order (...)`
- Many2one → integer FK column; One2many → no column (reverse FK); Many2many → junction table
- Standard columns `id, create_uid, create_date, write_uid, write_date` are automatic
- The `ir_*` tables form the meta-layer (models, fields, views, rules, access)
- Always index Many2one columns (Odoo does this automatically)

## 6.6 Interview Questions

**Q1: Where does Odoo store view XML definitions?**
> In the `ir_ui_view` table. When a module loads, its XML view files are parsed and each `<record model="ir.ui.view">` is inserted into this table. The ORM reads views from this table at runtime.

**Q2: What SQL does `order.order_line` access trigger?**
> `SELECT id FROM sale_order_line WHERE order_id = <order.id> ORDER BY sequence, id`. The `order_id` column is the Many2one FK on `sale_order_line`, and Odoo reads it as the inverse One2many.

**Q3: How does Many2many differ from One2many in the database?**
> One2many is a virtual field — the FK column lives on the "many" side model's table. Many2many creates a dedicated junction (relation) table with two FK columns, one for each side of the relationship. A Many2many record can be linked to many records on both sides simultaneously.

---

# CHAPTER 7: APIs AND COMMUNICATION

## 7.1 Overview of Odoo's API Interfaces

```
External Client
      │
      ├── XML-RPC   → /xmlrpc/2/common, /xmlrpc/2/object
      ├── JSON-RPC  → /web/dataset/call_kw  (main internal API)
      └── REST API  → /api/v1/...  (Odoo 17+)
```

## 7.2 XML-RPC: The Classic External API

XML-RPC is the traditional way external programs integrate with Odoo. It's been stable since TinyERP days and works over plain HTTP/HTTPS.

### 7.2.1 Authentication (Common Endpoint)

```python
import xmlrpc.client

url = 'http://localhost:8069'
db = 'mycompany'
username = 'admin'
password = 'admin'

# Step 1: Authenticate — get user ID
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
print(f'Authenticated as UID: {uid}')

# Check server version
version = common.version()
print(version)
# {'server_version': '16.0', 'server_version_info': [16, 0, ...]}
```

### 7.2.2 CRUD via XML-RPC

```python
# Step 2: Create the object endpoint proxy
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# ── SEARCH ─────────────────────────────────────────────────────
order_ids = models.execute_kw(
    db, uid, password,
    'sale.order',    # model
    'search',        # method
    [[('state', '=', 'sale')]],  # domain (positional args)
    {'limit': 10},               # kwargs
)
print(order_ids)  # [1, 2, 3, 42, ...]

# ── READ ──────────────────────────────────────────────────────
orders = models.execute_kw(
    db, uid, password,
    'sale.order', 'read',
    [order_ids],
    {'fields': ['name', 'partner_id', 'amount_total', 'state']},
)
for o in orders:
    print(o['name'], o['partner_id'][1], o['amount_total'])
    # o['partner_id'] → [5, 'ACME Corp'] (id, display_name)

# ── SEARCH_READ (combined) ─────────────────────────────────────
orders = models.execute_kw(
    db, uid, password,
    'sale.order', 'search_read',
    [[('state', 'in', ['sale', 'done'])]],
    {
        'fields': ['name', 'partner_id', 'amount_total'],
        'limit': 50,
        'order': 'date_order desc',
    },
)

# ── CREATE ────────────────────────────────────────────────────
new_id = models.execute_kw(
    db, uid, password,
    'sale.order', 'create',
    [{
        'partner_id': 7,
        'order_line': [
            (0, 0, {
                'product_id': 15,
                'product_uom_qty': 3,
                'price_unit': 100.0,
            }),
        ],
    }],
)
print(f'Created order ID: {new_id}')

# ── WRITE ─────────────────────────────────────────────────────
models.execute_kw(
    db, uid, password,
    'sale.order', 'write',
    [[new_id], {'note': 'Created via XML-RPC'}],
)

# ── UNLINK ────────────────────────────────────────────────────
result = models.execute_kw(
    db, uid, password,
    'sale.order', 'unlink',
    [[new_id]],
)

# ── CALL CUSTOM METHOD ────────────────────────────────────────
result = models.execute_kw(
    db, uid, password,
    'sale.order', 'action_confirm',
    [[new_id]],  # Pass list of IDs
)

# ── SEARCH_COUNT ──────────────────────────────────────────────
count = models.execute_kw(
    db, uid, password,
    'sale.order', 'search_count',
    [[('state', '=', 'sale')]],
)
```

### 7.2.3 Introspecting Model Fields via XML-RPC

```python
# Get all fields of a model (useful for exploration)
fields_info = models.execute_kw(
    db, uid, password,
    'sale.order', 'fields_get',
    [],
    {'attributes': ['string', 'type', 'required', 'readonly', 'selection']},
)
for field_name, info in fields_info.items():
    print(f'{field_name:25} {info["type"]:15} {info["string"]}')
```

## 7.3 JSON-RPC: The Frontend's Native Protocol

The Odoo frontend (and any modern integration) uses JSON-RPC over HTTP POST.

### 7.3.1 Protocol Structure

```json
// Request
POST /web/dataset/call_kw
Content-Type: application/json

{
    "jsonrpc": "2.0",
    "method": "call",
    "id": 1,
    "params": {
        "model": "sale.order",
        "method": "search_read",
        "args": [[["state", "=", "sale"]]],
        "kwargs": {
            "fields": ["name", "partner_id", "amount_total"],
            "limit": 10
        }
    }
}

// Response
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": [
        {"id": 1, "name": "S00001", "partner_id": [5, "ACME"], "amount_total": 1500.0},
        ...
    ]
}
```

### 7.3.2 Python Client for JSON-RPC

```python
import requests
import json

class OdooJSONRPC:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.session = requests.Session()
        self._authenticate(username, password)
    
    def _authenticate(self, username, password):
        resp = self.session.post(f'{self.url}/web/session/authenticate', json={
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'db': self.db,
                'login': username,
                'password': password,
            }
        })
        result = resp.json()
        self.uid = result['result']['uid']
    
    def call(self, model, method, args=None, kwargs=None):
        resp = self.session.post(f'{self.url}/web/dataset/call_kw', json={
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'model': model,
                'method': method,
                'args': args or [],
                'kwargs': kwargs or {},
            }
        })
        result = resp.json()
        if 'error' in result:
            raise Exception(result['error']['data']['message'])
        return result['result']

# Usage
client = OdooJSONRPC('http://localhost:8069', 'mydb', 'admin', 'admin')
orders = client.call('sale.order', 'search_read',
    args=[[['state', '=', 'sale']]],
    kwargs={'fields': ['name', 'amount_total']}
)
```

## 7.4 REST API (Odoo 17+)

Odoo 17 introduced a proper REST API. For earlier versions, use the `base_rest` or `djangoodoo` community modules.

```python
# Odoo 17 REST API
import requests

base_url = 'http://localhost:8069/api/v1'
headers = {'Content-Type': 'application/json'}

# Authenticate
auth = requests.post(f'{base_url}/auth/token', json={
    'db': 'mydb', 'login': 'admin', 'password': 'admin'
})
token = auth.json()['access_token']
headers['Authorization'] = f'Bearer {token}'

# GET records
response = requests.get(
    f'{base_url}/sale.order',
    headers=headers,
    params={'domain': '[["state","=","sale"]]', 'limit': 10}
)
orders = response.json()

# POST create
response = requests.post(
    f'{base_url}/sale.order',
    headers=headers,
    json={'partner_id': 5, 'date_order': '2024-01-15'}
)

# PUT update
response = requests.put(
    f'{base_url}/sale.order/42',
    headers=headers,
    json={'note': 'Updated via REST'}
)

# DELETE
response = requests.delete(f'{base_url}/sale.order/42', headers=headers)
```

## 7.5 Building a Custom Controller

```python
# my_module/controllers/main.py
from odoo import http
from odoo.http import request
import json

class MyController(http.Controller):
    
    @http.route('/my_api/orders', 
                type='json',          # 'json' or 'http'
                auth='user',          # 'user', 'public', 'none'
                methods=['POST'],
                csrf=False,)
    def get_orders(self, **kwargs):
        """JSON-RPC endpoint"""
        domain = kwargs.get('domain', [])
        orders = request.env['sale.order'].search_read(
            domain,
            fields=['name', 'partner_id', 'amount_total', 'state'],
        )
        return orders
    
    @http.route('/my_api/order/<int:order_id>',
                type='http',
                auth='public',
                methods=['GET'])
    def get_order(self, order_id, **kwargs):
        """HTTP endpoint returning JSON manually"""
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists():
            return request.make_response(
                json.dumps({'error': 'Not found'}),
                headers=[('Content-Type', 'application/json')],
                status=404
            )
        data = {
            'id': order.id,
            'name': order.name,
            'partner': order.partner_id.name,
            'total': order.amount_total,
        }
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )
    
    @http.route('/my_webhook', type='json', auth='none', csrf=False)
    def webhook_receiver(self, **payload):
        """Receive webhooks from external systems"""
        # Process payload without authentication (be careful!)
        order_ref = payload.get('reference')
        # ... process
        return {'status': 'received'}
```

## 7.6 Chapter Summary

- **XML-RPC** (`/xmlrpc/2/`): classic, stable, works with Python's `xmlrpc.client`
- **JSON-RPC** (`/web/dataset/call_kw`): used by the frontend, session-based auth
- **REST** (`/api/v1/`): new in Odoo 17, token-based
- Custom controllers use `@http.route` and `http.Controller`
- `type='json'` auto-serializes return values; `type='http'` for raw HTTP responses

## 7.7 Interview Questions

**Q1: What is the difference between XML-RPC and JSON-RPC in Odoo?**
> Both call the same underlying Python model methods. XML-RPC (`/xmlrpc/2/`) uses HTTP Basic/Digest authentication and XML encoding. JSON-RPC (`/web/dataset/call_kw`) uses session cookies and JSON encoding. JSON-RPC is used internally by the Odoo frontend. XML-RPC is preferred for external system integrations due to its stability.

**Q2: How do you expose a method to XML-RPC/JSON-RPC without making it callable from the web?**
> By convention, methods prefixed with `_` (underscore) are not callable from the web. The `check_method_name()` function in the controller layer blocks any method starting with `_`. To explicitly mark a method as public API, no special decorator is needed — just don't prefix it with `_`.

---

# CHAPTER 8: SECURITY MODEL

## 8.1 Security Architecture Overview

```
Request comes in
        │
        ▼
┌───────────────────────┐
│  Authentication       │  Is the user logged in?
│  (res.users / session)│  Valid session cookie?
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Model Access Control │  Can this user READ/WRITE/CREATE/DELETE
│  (ir.model.access)   │  records of THIS model at all?
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Record Rules         │  Of the records they can access at model
│  (ir.rule)           │  level, WHICH SPECIFIC RECORDS can they see?
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Field-Level Security │  (optional) Which FIELDS can they read/write?
│  (groups on fields)  │  via groups= attribute on field definition
└──────────┬────────────┘
           │
           ▼
         Result
```

## 8.2 Users and Groups

### 8.2.1 User Model (`res.users`)

```python
# Every login is a res.users record
# res.users inherits (delegate) from res.partner
# Key fields:
# - login: username for authentication
# - password: stored as bcrypt hash
# - groups_id: Many2many to res.groups
# - company_id: current active company
# - company_ids: all allowed companies
```

### 8.2.2 Groups (`res.groups`)

Groups are the core of Odoo's permission system. Every right is granted to a group, not to individual users.

```xml
<!-- security/security.xml -->
<odoo>
  <!-- Define a new group -->
  <record id="group_sale_manager" model="res.groups">
    <field name="name">Sales Manager</field>
    <field name="category_id" ref="base.module_category_sales"/>
    <!-- Implied groups: members of this group also get these groups -->
    <field name="implied_ids" eval="[(4, ref('group_sale_user'))]"/>
    <!-- Users in this group -->
    <field name="users" eval="[(4, ref('base.user_admin'))]"/>
  </record>
  
  <!-- Categories group the groups in Settings > Users -->
  <record id="module_category_sales" model="ir.module.category">
    <field name="name">Sales</field>
    <field name="sequence">15</field>
  </record>
</odoo>
```

```python
# Checking group membership in Python
class SaleOrder(models.Model):
    _name = 'sale.order'
    
    def action_cancel(self):
        # Check if user is in a specific group
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise AccessError("Only Sales Managers can cancel orders!")
        self.write({'state': 'cancel'})
    
    # Restrict a field to a group
    margin = fields.Float(
        'Margin',
        groups='sales_team.group_sale_manager',  # Only managers see this
    )
```

### 8.2.3 Standard Group Hierarchy (Sales Example)

```
base.group_user (Internal User)  ← All users inherit this
  └── sales_team.group_sale_salesman (User)
        └── sales_team.group_sale_manager (Manager)
              └── base.group_system (Administrator)
```

## 8.3 Access Control Lists (ACLs) — `ir.model.access`

ACLs define what operations a group can perform on a model.

### 8.3.1 The CSV Format

```csv
<!-- security/ir.model.access.csv -->
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sale_order_user,sale.order user,model_sale_order,sales_team.group_sale_salesman,1,1,1,0
access_sale_order_manager,sale.order manager,model_sale_order,sales_team.group_sale_manager,1,1,1,1
access_sale_order_public,sale.order public,model_sale_order,base.group_public,1,0,0,0
```

**Column meanings:**

| Column | Description |
|---|---|
| `id` | XML ID for this ACL record |
| `name` | Human-readable name |
| `model_id:id` | XML ID of the model (auto: `model_sale_order` for `sale.order`) |
| `group_id:id` | XML ID of the group. Empty = applies to ALL users |
| `perm_read` | 1=allowed, 0=denied |
| `perm_write` | 1=allowed, 0=denied |
| `perm_create` | 1=allowed, 0=denied |
| `perm_unlink` | 1=allowed, 0=denied |

### 8.3.2 ACL in Python (verifying)

```python
# ORM checks ACL before every operation automatically
# But you can check manually:
Model = self.env['sale.order']
can_create = Model.check_access_rights('create', raise_exception=False)
can_unlink = Model.check_access_rights('unlink', raise_exception=False)

# Force check (raises AccessError if denied):
self.env['account.move'].check_access_rights('write')
```

### 8.3.3 Where ACL is Enforced in the ORM

```python
# odoo/models.py (simplified)
class BaseModel:
    def create(self, vals_list):
        self.check_access_rights('create')    # ← ACL check
        self.check_access_rule('create')      # ← Record rule check
        # ... SQL INSERT ...
    
    def write(self, vals):
        self.check_access_rights('write')
        self.check_access_rule('write')
        # ... SQL UPDATE ...
    
    def unlink(self):
        self.check_access_rights('unlink')
        self.check_access_rule('unlink')
        # ... SQL DELETE ...
    
    def _search(self, domain, ...):
        self.check_access_rights('read')
        # Record rules are applied as WHERE clauses in search SQL
        # No separate check_access_rule needed for read
```

## 8.4 Record Rules (`ir.rule`)

While ACLs control model-level access, Record Rules control which **specific records** a user can access. They add a WHERE clause to every query.

### 8.4.1 Defining a Record Rule

```xml
<!-- security/security.xml -->
<record id="sale_order_rule_company" model="ir.rule">
    <field name="name">Sales Order: Company</field>
    <field name="model_id" ref="model_sale_order"/>
    
    <!-- The domain filter applied to every query -->
    <!-- 'company_id' in user.company_ids means: 
         only show orders from companies the user belongs to -->
    <field name="domain_force">
        [('company_id', 'in', company_ids)]
    </field>
    
    <!-- Which operations this rule applies to -->
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="True"/>
    
    <!-- Applied to these groups (empty = all users) -->
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
</record>
```

### 8.4.2 Domain Variables in Record Rules

In record rule domains, these variables are available:

```python
# Available variables in ir.rule domain_force:
user          # res.users record (current user)
time          # Python time module
company_id    # Current company ID (integer)
company_ids   # All allowed company IDs (list of ints)

# Example domains:
[('user_id', '=', user.id)]                    # Own records only
[('company_id', 'in', company_ids)]             # Multi-company filter
[('state', '!=', 'cancelled')]                  # No cancelled records
[('create_uid', '=', user.id)]                  # Own creations only
```

### 8.4.3 How Record Rules Generate SQL

```python
# When a user searches for sale.order records,
# the ORM adds record rule domains as WHERE conditions:

# User's search:
orders = env['sale.order'].search([('state', '=', 'sale')])

# ORM-generated SQL (with record rules applied):
# SELECT sale_order.id
# FROM sale_order
# WHERE (sale_order.state = 'sale')          ← User's domain
#   AND (sale_order.user_id = 3)            ← Record rule 1 (own records)
#   AND (sale_order.company_id IN (1, 2))   ← Record rule 2 (company filter)
```

### 8.4.4 Global vs Group Rules

```
Global Rule (no group):  applies to ALL users (AND-ed together)
Group Rule (with group): applies only to that group's users
                         Multiple group rules for same model are OR-ed
                         Global AND Group rules are AND-ed
```

**Logic:**
```
Final domain = Global Rule 1 AND Global Rule 2 AND (Group Rule A OR Group Rule B)
```

## 8.5 Field-Level Security

```python
# Python: restrict a field to a specific group
class SaleOrder(models.Model):
    _name = 'sale.order'
    
    # Only Sales Managers can see/edit the margin field
    margin = fields.Float(
        'Margin (%)',
        groups='sales_team.group_sale_manager',
    )
    
    # Multiple groups (comma-separated)
    cost_price = fields.Float(
        'Cost',
        groups='sales_team.group_sale_manager,account.group_account_manager',
    )
```

When a user without the required group reads a record, fields with `groups=` return `False` instead of their actual value.

## 8.6 `sudo()` — Bypassing Security

```python
# sudo() creates a new environment with superuser (uid=1)
# bypassing ALL access rights and record rules

# DANGER: Use with extreme caution!
# Only use when you explicitly need to bypass security

class ResPartner(models.Model):
    _name = 'res.partner'
    
    def _update_last_activity(self):
        """Called during website visitor tracking — needs to update
        partner records even for public user"""
        # Public user can't write to res.partner normally
        # sudo() lets this internal method bypass the check
        self.sudo().write({'last_activity': fields.Datetime.now()})
    
    # sudo() with specific user:
    admin = self.env.ref('base.user_admin')
    self.env['sale.order'].with_user(admin).create({...})
    
    # WRONG: Don't do this to bypass validation errors
    # self.sudo().write({'state': 'done'})  # BAD: bypasses constraints too?
    # Note: Python @api.constrains still runs with sudo(), only ACL is bypassed
```

## 8.7 Practical Security Example

```python
# Scenario: Sales users see only their own orders
#           Sales managers see all orders of their company

# Step 1: Define groups (security.xml)
# - sales_team.group_sale_salesman (User)
# - sales_team.group_sale_manager (Manager — implies salesman)

# Step 2: ACL (ir.model.access.csv)
# Salesmen: read=1, write=1, create=1, unlink=0
# Managers: read=1, write=1, create=1, unlink=1

# Step 3: Record Rules (security.xml)

# Global rule: everyone filtered to their company
# <domain_force>[('company_id', 'in', company_ids)]</domain_force>
# groups: (empty — global)

# Group rule for salesmen: only their own orders
# <domain_force>[('user_id', '=', user.id)]</domain_force>
# groups: sales_team.group_sale_salesman

# Group rule for managers: all company orders (no additional filter)
# <domain_force>[(1, '=', 1)]</domain_force>  ← True, no filter
# groups: sales_team.group_sale_manager

# Result:
# Salesman Joe: sees only orders where user_id = Joe AND company = Joe's company
# Manager Alice: sees all orders in her company
```

## 8.8 Chapter Summary

- Security is layered: Authentication → ACL → Record Rules → Field Groups
- ACL (`ir.model.access`) = can this group CRUD on this model at all?
- Record Rules (`ir.rule`) = which specific records can this user see?
- `groups=` on fields = which fields can this group see/edit?
- `sudo()` bypasses ALL access control — use carefully and only for legitimate internal logic
- Multiple group record rules are OR-ed; global rules are AND-ed with group rules

## 8.9 Interview Questions

**Q1: What is the difference between ACL and Record Rules?**
> ACL (ir.model.access) is model-level: it controls whether a group can perform CRUD at all on a model. Record Rules (ir.rule) are record-level: they add a WHERE clause to queries, restricting which specific records a user can see. A user can have read access to `sale.order` (ACL) but only see their own orders (Record Rule).

**Q2: What happens when no ACL exists for a model?**
> If no ACL record exists for a model and the user is not an administrator, access is DENIED. Odoo fails closed: no ACL = no access. This is why every new model must have an `ir.model.access.csv` entry.

**Q3: How do record rules impact performance?**
> Record rules are translated into additional WHERE conditions added to every SQL query. Poorly written rules (e.g., with subqueries or complex joins) can severely degrade performance. Always ensure the fields used in record rule domains are indexed.

---

# CHAPTER 9: SCHEDULED JOBS, SERVER ACTIONS, AND AUTOMATION

## 9.1 Scheduled Actions (`ir.cron`)

Odoo has a built-in task scheduler stored in the `ir_cron` table. There is no external task queue (no Celery, no Redis).

### 9.1.1 How `ir.cron` Works

```
Odoo Worker Process (cron worker)
  │
  ├── Every 1 minute: check ir_cron table
  │   SELECT id FROM ir_cron
  │   WHERE active = TRUE
  │     AND nextcall <= NOW()
  │     AND user_id IS NOT NULL
  │
  ├── For each due cron:
  │   ├── Lock the row: SELECT ... FOR UPDATE SKIP LOCKED
  │   ├── Execute the Python method
  │   ├── Update nextcall = nextcall + interval
  │   └── Commit
  └── Sleep
```

### 9.1.2 Defining a Cron Job in XML

```xml
<!-- data/cron.xml -->
<odoo>
  <record id="cron_auto_confirm_orders" model="ir.cron">
    <field name="name">Auto Confirm Draft Orders</field>
    <field name="model_id" ref="sale.model_sale_order"/>
    <field name="state">code</field>    <!-- 'code' or 'object' -->
    
    <!-- Python code to execute -->
    <field name="code">
      model.auto_confirm_old_orders()
    </field>
    
    <!-- Interval -->
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>  <!-- minutes, hours, days, weeks, months -->
    
    <!-- First execution -->
    <field name="nextcall">2024-01-01 06:00:00</field>
    
    <!-- Run as this user -->
    <field name="user_id" ref="base.user_admin"/>
    
    <field name="active">True</field>
    <field name="numbercall">-1</field>  <!-- -1 = run indefinitely -->
  </record>
</odoo>
```

### 9.1.3 Implementing the Cron Method

```python
# models/sale_order.py
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'
    
    @api.model
    def auto_confirm_old_orders(self):
        """
        Cron job: Confirm orders that have been in draft for more than 7 days.
        Called by ir.cron with model = sale.order.
        
        Uses @api.model because it's called on the class, not a specific recordset.
        """
        _logger.info("Running auto_confirm_old_orders cron job")
        
        cutoff_date = fields.Datetime.subtract(
            fields.Datetime.now(), days=7
        )
        
        # Find old draft orders
        old_drafts = self.search([
            ('state', '=', 'draft'),
            ('create_date', '<', cutoff_date),
        ])
        
        if not old_drafts:
            _logger.info("No old draft orders found")
            return
        
        _logger.info(f"Found {len(old_drafts)} orders to confirm")
        
        # Process in batches to avoid timeout
        for order in old_drafts:
            try:
                order.action_confirm()
                _logger.info(f"Confirmed order: {order.name}")
            except Exception as e:
                _logger.error(f"Failed to confirm {order.name}: {e}")
                # Continue with next order even if one fails
        
        _logger.info("auto_confirm_old_orders completed")
```

### 9.1.4 Cron with Savepoints (Partial Success)

```python
@api.model
def process_orders_safely(self):
    """Process each order in its own savepoint so failures don't roll back all"""
    orders = self.search([('state', '=', 'draft')])
    
    for order in orders:
        try:
            with self.env.cr.savepoint():
                order.action_confirm()
                # If this raises, only this savepoint is rolled back
        except Exception as e:
            _logger.error(f"Failed processing order {order.name}: {e}")
            # Continue with next order
```

## 9.2 Server Actions (`ir.actions.server`)

Server Actions are configurable automation that can be:
- Triggered manually (button in UI)
- Linked to automation rules
- Called from wizards

### 9.2.1 Defining a Server Action

```xml
<!-- data/data.xml -->
<record id="action_send_confirmation_email" model="ir.actions.server">
    <field name="name">Send Confirmation Email</field>
    <field name="model_id" ref="sale.model_sale_order"/>
    <field name="state">code</field>
    <field name="code">
        for record in records:
            record.action_send_confirmation()
    </field>
    <!-- Binding: show this action in the Actions menu on sale.order list/form -->
    <field name="binding_model_id" ref="sale.model_sale_order"/>
    <field name="binding_type">action</field>  <!-- 'action' or 'report' -->
</record>
```

### 9.2.2 Server Action Types

| `state` value | Description |
|---|---|
| `code` | Run Python code (`record`, `records`, `env` available) |
| `object_create` | Create a new record |
| `object_write` | Write values to current records |
| `multi` | Run multiple child server actions |
| `email` | Send email using a template |
| `sms` | Send SMS |
| `next` | Return a window action |

## 9.3 Automation Rules (`base.automation`)

Automation Rules (requires the `base_automation` module) trigger server actions based on model events.

### 9.3.1 Automation in XML

```xml
<record id="auto_send_email_on_confirm" model="base.automation">
    <field name="name">Send Email When Order Confirmed</field>
    <field name="model_id" ref="sale.model_sale_order"/>
    
    <!-- Trigger options:
         on_create, on_write, on_create_or_write,
         on_unlink, on_change, based_on_timed_condition,
         on_stage_set, on_user_set -->
    <field name="trigger">on_write</field>
    
    <!-- Only trigger when state changes to 'sale' -->
    <field name="filter_pre_domain">[('state', '!=', 'sale')]</field>
    <field name="filter_domain">[('state', '=', 'sale')]</field>
    
    <!-- Action to run -->
    <field name="action_server_ids" eval="[(4, ref('action_send_confirmation_email'))]"/>
</record>
```

### 9.3.2 Automation with Timed Condition

```xml
<!-- Trigger 3 days after date_deadline if task not done -->
<record id="auto_remind_overdue_tasks" model="base.automation">
    <field name="name">Remind Overdue Tasks</field>
    <field name="model_id" ref="project.model_project_task"/>
    <field name="trigger">based_on_timed_condition</field>
    <field name="date_field_name">date_deadline</field>
    <field name="trg_date_id" ref="project.model_project_task.date_deadline"/>
    <field name="trg_date_range">3</field>
    <field name="trg_date_range_type">days</field>
    <field name="filter_domain">[('stage_id.name', '!=', 'Done')]</field>
    <field name="action_server_ids" eval="[(4, ref('action_notify_overdue'))]"/>
</record>
```

## 9.4 Manual Triggering from Python

```python
class SaleOrder(models.Model):
    _name = 'sale.order'
    
    def trigger_server_action(self):
        """Manually trigger a server action programmatically"""
        action = self.env.ref('my_module.action_send_confirmation_email')
        action.with_context(active_ids=self.ids, active_model=self._name).run()
    
    def run_cron_manually(self):
        """Trigger a cron job manually (useful for testing)"""
        cron = self.env.ref('my_module.cron_auto_confirm_orders')
        cron.sudo()._callback(
            cron.model_id.model,
            cron._get_callback_hash(),
            cron.id
        )
```

## 9.5 Logging Best Practices

```python
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _name = 'sale.order'
    
    def process(self):
        _logger.debug("Debug info (not shown in production)")
        _logger.info("Informational message")
        _logger.warning("Something unexpected but handled")
        _logger.error("Error occurred: %s", error_detail)
        _logger.exception("Error with traceback:")  # logs traceback automatically
```

## 9.6 Chapter Summary

- `ir.cron` is Odoo's built-in scheduler — no Celery/Redis needed
- Cron methods use `@api.model` and run in a dedicated worker process
- Server Actions (`ir.actions.server`) run Python code against records
- Automation Rules (`base.automation`) trigger server actions on model events
- Use `cr.savepoint()` in cron jobs to allow partial success without full rollback
- Always use `_logger = logging.getLogger(__name__)` for structured logging

## 9.7 Interview Questions

**Q1: How does Odoo prevent two cron workers from executing the same cron job simultaneously?**
> Odoo uses PostgreSQL's `SELECT ... FOR UPDATE SKIP LOCKED`. When a cron worker picks up a job, it locks the `ir_cron` row. Other workers skip locked rows. This prevents duplicate execution without any external lock manager.

**Q2: What is the difference between `ir.cron` and `base.automation`?**
> `ir.cron` is time-based: it runs at a scheduled interval (every hour, every day). `base.automation` is event-based: it triggers when a record is created, written, deleted, or a field changes. They can work together: a cron job can also trigger automation rules.

---

# CHAPTER 10: CUSTOM MODULE DEVELOPMENT

## 10.1 Development Setup

```bash
# Clone Odoo
git clone https://github.com/odoo/odoo.git --depth=1 --branch=16.0

# Install Python dependencies
pip install -r requirements.txt --break-system-packages

# Create a PostgreSQL database
createdb myodoo

# Initialize the database
python odoo-bin -d myodoo --addons-path=addons -i base --stop-after-init

# Run Odoo in development mode
python odoo-bin -d myodoo \
  --addons-path=addons,/path/to/my/custom/addons \
  --dev=xml,reload,qweb \
  --log-level=debug
```

**Key dev flags:**
- `--dev=xml`: reload XML files without restart
- `--dev=reload`: auto-reload Python on file change
- `--dev=all`: all development features

## 10.2 Complete Custom Module: `library_management`

Let's build a complete module for managing a library's book catalog.

### 10.2.1 File Structure

```
library_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── library_book.py
│   └── library_member.py
├── views/
│   ├── library_book_views.xml
│   ├── library_member_views.xml
│   └── menus.xml
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
├── data/
│   └── sequences.xml
├── wizards/
│   ├── __init__.py
│   └── book_borrow_wizard.py
└── report/
    └── book_report_views.xml
```

### 10.2.2 `__manifest__.py`

```python
{
    'name': 'Library Management',
    'version': '16.0.1.0.0',
    'category': 'Services',
    'summary': 'Manage library books, members, and borrowing',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/library_book_views.xml',
        'views/library_member_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

### 10.2.3 `models/library_book.py`

```python
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'title'
    _rec_name = 'title'

    # ── BASIC FIELDS ─────────────────────────────────────────────
    title = fields.Char(
        string='Title',
        required=True,
        index=True,
        tracking=True,
    )
    isbn = fields.Char(
        string='ISBN',
        index=True,
        copy=False,
    )
    author_ids = fields.Many2many(
        'res.partner',
        'library_book_author_rel',
        'book_id',
        'author_id',
        string='Authors',
        domain=[('is_company', '=', False)],
    )
    publisher_id = fields.Many2one(
        'res.partner',
        string='Publisher',
        domain=[('is_company', '=', True)],
    )
    date_published = fields.Date(string='Publication Date')
    pages = fields.Integer(string='Number of Pages')
    cover = fields.Binary(string='Cover Image', attachment=True)
    description = fields.Html(string='Description')
    
    # ── CATEGORIZATION ───────────────────────────────────────────
    category = fields.Selection([
        ('fiction', 'Fiction'),
        ('non_fiction', 'Non-Fiction'),
        ('science', 'Science'),
        ('history', 'History'),
        ('technology', 'Technology'),
        ('biography', 'Biography'),
    ], string='Category', required=True, default='fiction')

    # ── STATE MANAGEMENT ─────────────────────────────────────────
    state = fields.Selection([
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
    ], string='State', default='available', tracking=True, index=True)

    # ── RELATIONSHIPS ────────────────────────────────────────────
    borrow_ids = fields.One2many(
        'library.borrow',
        'book_id',
        string='Borrow History',
    )
    
    current_borrower_id = fields.Many2one(
        'library.member',
        compute='_compute_current_borrower',
        string='Current Borrower',
        store=True,
    )

    # ── COMPUTED FIELDS ──────────────────────────────────────────
    borrow_count = fields.Integer(
        string='Times Borrowed',
        compute='_compute_borrow_count',
        store=True,
    )
    
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
    )

    # ── SEQUENCE ─────────────────────────────────────────────────
    ref = fields.Char(
        string='Reference',
        copy=False,
        readonly=True,
        default='New',
    )

    # ── SQL CONSTRAINTS ──────────────────────────────────────────
    _sql_constraints = [
        ('isbn_unique', 'UNIQUE(isbn)', 'ISBN must be unique!'),
    ]

    # ── COMPUTED FIELD IMPLEMENTATIONS ───────────────────────────
    @api.depends('borrow_ids', 'borrow_ids.state')
    def _compute_current_borrower(self):
        for book in self:
            active_borrow = book.borrow_ids.filtered(
                lambda b: b.state == 'borrowed'
            )
            book.current_borrower_id = active_borrow[:1].member_id if active_borrow else False

    @api.depends('borrow_ids')
    def _compute_borrow_count(self):
        for book in self:
            book.borrow_count = len(book.borrow_ids)

    def _compute_is_overdue(self):
        today = fields.Date.today()
        for book in self:
            overdue_borrows = book.borrow_ids.filtered(
                lambda b: b.state == 'borrowed' and b.due_date and b.due_date < today
            )
            book.is_overdue = bool(overdue_borrows)

    # ── CONSTRAINTS ──────────────────────────────────────────────
    @api.constrains('pages')
    def _check_pages(self):
        for book in self:
            if book.pages and book.pages < 0:
                raise ValidationError("Number of pages cannot be negative!")

    # ── LIFECYCLE HOOKS ──────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('library.book') or 'New'
        return super().create(vals_list)

    # ── BUSINESS METHODS ─────────────────────────────────────────
    def action_available(self):
        for book in self:
            if book.state == 'borrowed':
                raise UserError(f"Book '{book.title}' is currently borrowed. Return it first.")
            book.write({'state': 'available'})

    def action_maintenance(self):
        self.write({'state': 'maintenance'})

    def action_retire(self):
        for book in self:
            if book.state == 'borrowed':
                raise UserError(f"Cannot retire a borrowed book.")
        self.write({'state': 'retired'})

    def action_open_borrow_wizard(self):
        """Open the borrowing wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Borrow Book',
            'res_model': 'library.borrow.wizard',
            'view_mode': 'form',
            'target': 'new',   # Open as dialog
            'context': {
                'default_book_id': self.id,
            },
        }

    def action_view_borrows(self):
        """Smart button to view borrow history"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Borrow History',
            'res_model': 'library.borrow',
            'view_mode': 'list,form',
            'domain': [('book_id', '=', self.id)],
        }

    # ── NAME SEARCH OVERRIDE ─────────────────────────────────────
    @api.model
    def _name_search(self, name='', domain=None, operator='ilike', limit=100, name_get_uid=None):
        """Allow searching by title OR ISBN"""
        domain = domain or []
        if name:
            domain = ['|', ('title', operator, name), ('isbn', operator, name)] + domain
        return self._search(domain, limit=limit, access_rights_uid=name_get_uid)
```

### 10.2.4 `models/library_member.py`

```python
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LibraryMember(models.Model):
    _name = 'library.member'
    _description = 'Library Member'
    _inherit = ['mail.thread']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        required=True,
        ondelete='cascade',
    )
    membership_date = fields.Date(
        string='Membership Since',
        default=fields.Date.today,
    )
    expiry_date = fields.Date(string='Expiry Date')
    
    state = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ], string='Status', default='active', tracking=True)
    
    borrow_ids = fields.One2many(
        'library.borrow',
        'member_id',
        string='Borrowed Books',
    )
    
    active_borrows = fields.Integer(
        compute='_compute_active_borrows',
        string='Active Borrows',
        store=True,
    )
    
    max_borrows = fields.Integer(
        string='Max Books Allowed',
        default=3,
    )

    # Delegate name, email to partner
    name = fields.Char(related='partner_id.name', store=True, string='Name')
    email = fields.Char(related='partner_id.email', string='Email')
    phone = fields.Char(related='partner_id.phone', string='Phone')

    @api.depends('borrow_ids', 'borrow_ids.state')
    def _compute_active_borrows(self):
        for member in self:
            member.active_borrows = len(
                member.borrow_ids.filtered(lambda b: b.state == 'borrowed')
            )

    @api.constrains('max_borrows')
    def _check_max_borrows(self):
        for member in self:
            if member.max_borrows < 1:
                raise ValidationError("Member must be allowed to borrow at least 1 book.")

    def can_borrow(self):
        """Return True if member can borrow more books"""
        self.ensure_one()
        if self.state != 'active':
            return False, f"Member {self.name} is {self.state}"
        if self.active_borrows >= self.max_borrows:
            return False, f"Member {self.name} has reached their borrow limit ({self.max_borrows})"
        return True, ""


class LibraryBorrow(models.Model):
    _name = 'library.borrow'
    _description = 'Book Borrow Record'
    _order = 'borrow_date desc'

    book_id = fields.Many2one('library.book', required=True, ondelete='cascade')
    member_id = fields.Many2one('library.member', required=True, ondelete='cascade')
    borrow_date = fields.Date(default=fields.Date.today, string='Borrow Date')
    due_date = fields.Date(string='Due Date')
    return_date = fields.Date(string='Return Date')
    
    state = fields.Selection([
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ], default='borrowed', string='State')
    
    notes = fields.Text('Notes')
    
    days_borrowed = fields.Integer(
        compute='_compute_days',
        string='Days Borrowed',
    )

    @api.depends('borrow_date', 'return_date')
    def _compute_days(self):
        for borrow in self:
            if borrow.borrow_date:
                end = borrow.return_date or fields.Date.today()
                borrow.days_borrowed = (end - borrow.borrow_date).days
            else:
                borrow.days_borrowed = 0

    def action_return(self):
        """Mark book as returned"""
        for borrow in self:
            borrow.write({
                'state': 'returned',
                'return_date': fields.Date.today(),
            })
            borrow.book_id.write({'state': 'available'})
```

### 10.2.5 `wizards/book_borrow_wizard.py`

```python
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date, timedelta


class LibraryBorrowWizard(models.TransientModel):
    _name = 'library.borrow.wizard'
    _description = 'Borrow Book Wizard'

    book_id = fields.Many2one('library.book', string='Book', required=True)
    member_id = fields.Many2one('library.member', string='Member', required=True)
    borrow_days = fields.Integer(string='Borrow Duration (days)', default=14)
    due_date = fields.Date(string='Due Date', compute='_compute_due_date', store=True)
    notes = fields.Text('Notes')

    @api.depends('borrow_days')
    def _compute_due_date(self):
        for wizard in self:
            wizard.due_date = fields.Date.today() + timedelta(days=wizard.borrow_days)

    @api.onchange('book_id')
    def _onchange_book_id(self):
        if self.book_id and self.book_id.state != 'available':
            return {
                'warning': {
                    'title': 'Book Not Available',
                    'message': f'"{self.book_id.title}" is currently {self.book_id.state}',
                }
            }

    def action_confirm_borrow(self):
        """Confirm the borrowing"""
        self.ensure_one()
        
        # Validate book availability
        if self.book_id.state != 'available':
            raise UserError(f'Book "{self.book_id.title}" is not available.')
        
        # Validate member can borrow
        can_borrow, message = self.member_id.can_borrow()
        if not can_borrow:
            raise UserError(message)
        
        # Create borrow record
        borrow = self.env['library.borrow'].create({
            'book_id': self.book_id.id,
            'member_id': self.member_id.id,
            'due_date': self.due_date,
            'notes': self.notes,
        })
        
        # Update book state
        self.book_id.write({'state': 'borrowed'})
        
        # Return action to open the created record
        return {
            'type': 'ir.actions.act_window',
            'name': 'Borrow Record',
            'res_model': 'library.borrow',
            'view_mode': 'form',
            'res_id': borrow.id,
        }
```

### 10.2.6 `security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_library_book_user,library.book user,model_library_book,base.group_user,1,0,0,0
access_library_book_librarian,library.book librarian,model_library_book,base.group_system,1,1,1,1
access_library_member_user,library.member user,model_library_member,base.group_user,1,0,0,0
access_library_member_librarian,library.member librarian,model_library_member,base.group_system,1,1,1,1
access_library_borrow_user,library.borrow user,model_library_borrow,base.group_user,1,0,0,0
access_library_borrow_librarian,library.borrow librarian,model_library_borrow,base.group_system,1,1,1,1
access_library_borrow_wizard,library.borrow.wizard all,model_library_borrow_wizard,base.group_user,1,1,1,1
```

### 10.2.7 `data/sequences.xml`

```xml
<odoo>
  <data noupdate="1">
    <record id="seq_library_book" model="ir.sequence">
        <field name="name">Library Book Reference</field>
        <field name="code">library.book</field>
        <field name="prefix">LIB/%(year)s/</field>
        <field name="padding">4</field>
        <field name="number_increment">1</field>
        <!-- Result: LIB/2024/0001, LIB/2024/0002, ... -->
    </record>
  </data>
</odoo>
```

### 10.2.8 `views/library_book_views.xml`

```xml
<odoo>
  <!-- FORM VIEW -->
  <record id="view_library_book_form" model="ir.ui.view">
    <field name="name">library.book.form</field>
    <field name="model">library.book</field>
    <field name="arch" type="xml">
      <form string="Book">
        <!-- Status bar with state buttons -->
        <header>
          <button name="action_available" string="Set Available" 
                  type="object" class="btn-success"
                  invisible="state == 'available'"/>
          <button name="action_maintenance" string="Maintenance" 
                  type="object"
                  invisible="state in ['maintenance', 'retired']"/>
          <button name="action_retire" string="Retire" 
                  type="object" class="btn-danger"
                  groups="base.group_system"
                  invisible="state == 'retired'"/>
          <button name="action_open_borrow_wizard" string="Borrow" 
                  type="object" class="btn-primary"
                  invisible="state != 'available'"/>
          <field name="state" widget="statusbar" 
                 statusbar_visible="available,borrowed,maintenance"/>
        </header>
        
        <sheet>
          <!-- Smart buttons (top-right stats) -->
          <div class="oe_button_box" name="button_box">
            <button name="action_view_borrows" type="object" 
                    class="oe_stat_button" icon="fa-book">
              <field name="borrow_count" widget="statinfo" string="Borrows"/>
            </button>
          </div>
          
          <!-- Cover image -->
          <field name="cover" widget="image" class="oe_avatar"/>
          
          <div class="oe_title">
            <h1><field name="title" placeholder="Book Title"/></h1>
          </div>
          
          <group>
            <group>
              <field name="ref" readonly="1"/>
              <field name="isbn"/>
              <field name="category"/>
              <field name="pages"/>
            </group>
            <group>
              <field name="publisher_id"/>
              <field name="date_published"/>
              <field name="author_ids" widget="many2many_tags"/>
              <field name="current_borrower_id" readonly="1"/>
            </group>
          </group>
          
          <notebook>
            <page string="Description">
              <field name="description" widget="html"/>
            </page>
            <page string="Borrow History">
              <field name="borrow_ids" readonly="1">
                <list>
                  <field name="member_id"/>
                  <field name="borrow_date"/>
                  <field name="due_date"/>
                  <field name="return_date"/>
                  <field name="state"/>
                  <field name="days_borrowed"/>
                </list>
              </field>
            </page>
          </notebook>
        </sheet>
        
        <!-- Chatter (from mail.thread mixin) -->
        <div class="oe_chatter">
          <field name="message_follower_ids"/>
          <field name="activity_ids"/>
          <field name="message_ids"/>
        </div>
      </form>
    </field>
  </record>

  <!-- LIST VIEW -->
  <record id="view_library_book_list" model="ir.ui.view">
    <field name="name">library.book.list</field>
    <field name="model">library.book</field>
    <field name="arch" type="xml">
      <list string="Books" decoration-danger="is_overdue" 
            decoration-muted="state == 'retired'">
        <field name="ref"/>
        <field name="title"/>
        <field name="category"/>
        <field name="author_ids" widget="many2many_tags"/>
        <field name="publisher_id"/>
        <field name="state" widget="badge"
               decoration-success="state == 'available'"
               decoration-warning="state == 'borrowed'"
               decoration-danger="state == 'maintenance'"/>
        <field name="borrow_count"/>
        <field name="is_overdue" optional="hide"/>
      </list>
    </field>
  </record>

  <!-- KANBAN VIEW -->
  <record id="view_library_book_kanban" model="ir.ui.view">
    <field name="name">library.book.kanban</field>
    <field name="model">library.book</field>
    <field name="arch" type="xml">
      <kanban class="o_kanban_mobile" group_by="category">
        <field name="title"/>
        <field name="state"/>
        <field name="cover"/>
        <field name="author_ids"/>
        <templates>
          <t t-name="kanban-box">
            <div class="oe_kanban_card">
              <div class="o_kanban_image">
                <img t-att-src="kanban_image('library.book', 'cover', record.id.raw_value)"
                     alt="Cover"/>
              </div>
              <div class="oe_kanban_details">
                <strong><field name="title"/></strong>
                <div><field name="author_ids" widget="many2many_tags"/></div>
                <div class="o_kanban_tags_section">
                  <field name="state" widget="label_selection"/>
                </div>
              </div>
            </div>
          </t>
        </templates>
      </kanban>
    </field>
  </record>

  <!-- SEARCH VIEW -->
  <record id="view_library_book_search" model="ir.ui.view">
    <field name="name">library.book.search</field>
    <field name="model">library.book</field>
    <field name="arch" type="xml">
      <search string="Books">
        <field name="title"/>
        <field name="isbn"/>
        <field name="author_ids"/>
        <filter string="Available" name="filter_available" 
                domain="[('state', '=', 'available')]"/>
        <filter string="Borrowed" name="filter_borrowed" 
                domain="[('state', '=', 'borrowed')]"/>
        <filter string="Overdue" name="filter_overdue" 
                domain="[('is_overdue', '=', True)]"/>
        <separator/>
        <filter string="Fiction" name="filter_fiction" 
                domain="[('category', '=', 'fiction')]"/>
        <group expand="0" string="Group By">
          <filter string="Category" name="group_category" context="{'group_by': 'category'}"/>
          <filter string="State" name="group_state" context="{'group_by': 'state'}"/>
          <filter string="Publisher" name="group_publisher" context="{'group_by': 'publisher_id'}"/>
        </group>
      </search>
    </field>
  </record>

  <!-- ACTION (Window Action) -->
  <record id="action_library_book" model="ir.actions.act_window">
    <field name="name">Books</field>
    <field name="res_model">library.book</field>
    <field name="view_mode">kanban,list,form</field>
    <field name="search_view_id" ref="view_library_book_search"/>
    <field name="context">{'search_default_filter_available': 1}</field>
    <field name="help" type="html">
      <p class="o_view_nocontent_smiling_face">
        Add your first book!
      </p>
    </field>
  </record>
</odoo>
```

### 10.2.9 `views/menus.xml`

```xml
<odoo>
  <!-- Top-level menu -->
  <menuitem id="menu_library_root"
            name="Library"
            web_icon="library_management,static/description/icon.png"
            sequence="50"/>

  <!-- Second level -->
  <menuitem id="menu_library_catalog"
            name="Catalog"
            parent="menu_library_root"
            sequence="1"/>
  
  <menuitem id="menu_library_members"
            name="Members"
            parent="menu_library_root"
            sequence="2"/>

  <!-- Third level (actual links) -->
  <menuitem id="menu_library_books"
            name="Books"
            parent="menu_library_catalog"
            action="action_library_book"
            sequence="1"/>
</odoo>
```

## 10.3 Installing and Updating the Module

```bash
# Install
python odoo-bin -d myodoo -i library_management --stop-after-init

# Update (after changing Python code or XML)
python odoo-bin -d myodoo -u library_management --stop-after-init

# Run server with the module active
python odoo-bin -d myodoo --addons-path=addons,/path/to/custom/addons
```

## 10.4 Writing Tests

```python
# tests/test_library_book.py
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

@tagged('library', '-at_install', 'post_install')
class TestLibraryBook(TransactionCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test data once for the class
        cls.publisher = cls.env['res.partner'].create({
            'name': 'Test Publisher',
            'is_company': True,
        })
        cls.author = cls.env['res.partner'].create({
            'name': 'Test Author',
        })
        cls.book = cls.env['library.book'].create({
            'title': 'Test Book',
            'isbn': '978-0-123456-00-0',
            'category': 'fiction',
            'publisher_id': cls.publisher.id,
            'author_ids': [(4, cls.author.id)],
        })
        cls.member = cls.env['library.member'].create({
            'partner_id': cls.env['res.partner'].create({'name': 'Test Member'}).id,
        })
    
    def test_book_creation(self):
        """Test that a book is created with correct defaults"""
        self.assertEqual(self.book.state, 'available')
        self.assertNotEqual(self.book.ref, 'New')   # Sequence was applied
        self.assertTrue(self.book.ref.startswith('LIB/'))
    
    def test_duplicate_isbn_raises(self):
        """Test SQL constraint: duplicate ISBN raises IntegrityError"""
        with self.assertRaises(Exception):
            self.env['library.book'].create({
                'title': 'Another Book',
                'isbn': '978-0-123456-00-0',  # Same ISBN
                'category': 'fiction',
            })
    
    def test_borrow_workflow(self):
        """Test full borrow and return workflow"""
        # Book starts available
        self.assertEqual(self.book.state, 'available')
        
        # Create borrow record
        borrow = self.env['library.borrow'].create({
            'book_id': self.book.id,
            'member_id': self.member.id,
        })
        self.book.write({'state': 'borrowed'})
        
        self.assertEqual(self.book.state, 'borrowed')
        self.assertEqual(self.book.current_borrower_id, self.member)
        
        # Return the book
        borrow.action_return()
        
        self.assertEqual(self.book.state, 'available')
        self.assertEqual(borrow.state, 'returned')
        self.assertFalse(self.book.current_borrower_id)
    
    def test_cannot_retire_borrowed_book(self):
        """Test business rule: cannot retire a borrowed book"""
        self.book.write({'state': 'borrowed'})
        
        with self.assertRaises(UserError) as cm:
            self.book.action_retire()
        
        self.assertIn('Cannot retire a borrowed book', str(cm.exception))
    
    def test_negative_pages_raises(self):
        """Test Python constraint on pages field"""
        with self.assertRaises(ValidationError):
            self.book.write({'pages': -10})

# Run tests:
# python odoo-bin -d testdb --test-enable --stop-after-init -u library_management
# python odoo-bin -d testdb -u library_management --test-tags=library
```

## 10.5 Chapter Summary

- A complete module needs: `__manifest__.py`, models, views, security files
- Use `@api.model_create_multi` to override `create()` for sequence injection
- TransientModel (wizards) are temporary records used for dialog UI
- Tests use `TransactionCase` — every test runs in a rolled-back transaction
- Install: `-i module_name`, Update: `-u module_name`
- Views: form, list, kanban, search — all defined as XML `ir.ui.view` records

## 10.6 Interview Questions

**Q1: What is the difference between `models.Model` and `models.TransientModel`?**
> Both store records in PostgreSQL. `models.Model` records persist indefinitely. `TransientModel` records are temporary — Odoo's vacuum cron job (`base.autovacuum`) periodically deletes old TransientModel records (default: after 1 hour). Use TransientModel for wizard dialogs where you don't want to keep the data.

**Q2: What does `noupdate="1"` mean in XML data files?**
> `<data noupdate="1">` means the records inside are only created if they don't already exist. On module upgrade (`-u`), these records are NOT updated even if the XML changed. Used for sequences, default data, and records users might customize. Without it, every upgrade overwrites user changes.

**Q3: How do you add a field to an existing view from another module?**
> Use `inherit_id` to reference the original view and XPath expressions to locate insertion points. `position="after"` inserts after the target, `position="before"` before it, `position="replace"` replaces it, `position="attributes"` modifies attributes.
