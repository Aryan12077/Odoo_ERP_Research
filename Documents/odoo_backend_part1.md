# Exploration of the Odoo Backend Using Python
## A Complete Technical Textbook

**Author:** Senior Odoo Backend Architect  
**Version:** 1.0  
**Target Odoo Version:** 16/17 Community & Enterprise  
**Prerequisite:** Strong Python knowledge, basic SQL familiarity

---

# TABLE OF CONTENTS

- Chapter 1: What Is Odoo and Why Is It an ERP?
- Chapter 2: High-Level Architecture
- Chapter 3: Complete Request Lifecycle
- Chapter 4: Project Structure and Module Architecture
- Chapter 5: Python Backend Internals (Models, Fields, ORM, CRUD, Inheritance)
- Chapter 6: PostgreSQL Database Schema
- Chapter 7: APIs and Communication
- Chapter 8: Security Model
- Chapter 9: Scheduled Jobs, Server Actions, Automation
- Chapter 10: Custom Module Development
- Chapter 11: Debugging and Inspection
- Chapter 12: Exploring an Existing Codebase
- Chapter 13: Best Practices
- Chapter 14: Common Pitfalls
- Chapter 15: Roadmap to Productivity
- Part II: Technical Report

---

# CHAPTER 1: WHAT IS ODOO AND WHY IS IT AN ERP?

## 1.1 Concept: What Is Odoo?

Odoo is an open-source, modular Enterprise Resource Planning (ERP) platform written primarily in Python (backend) and JavaScript (frontend). Originally named TinyERP (2005) → OpenERP (2009) → Odoo (2014), it has grown into one of the world's most widely deployed ERP systems.

Odoo covers every business function through installable modules (also called apps):
- **Sales** (CRM, Quotations, Sales Orders)
- **Inventory** (Warehousing, Stock Moves, Reordering)
- **Accounting** (Journals, Invoices, Ledgers, Taxes)
- **Manufacturing** (Bills of Materials, Work Orders, MRP)
- **Human Resources** (Employees, Payroll, Leaves, Recruitment)
- **E-commerce, Point of Sale, Project, Helpdesk** and 30+ more

## 1.2 Why Is It an ERP?

An ERP (Enterprise Resource Planning) system integrates all departments of a company into a single unified data store and process engine. Instead of each department running its own isolated software (CRM for sales, separate accounting software, separate HR system), an ERP shares one database where every transaction is visible across departments.

**Example flow showing ERP integration:**
```
Customer places order (Sales)
  → Stock is reserved (Inventory)
    → Manufacturing order triggered (Manufacturing)
      → Payroll hours recorded (HR)
        → Invoice generated (Accounting)
          → Payment matched (Accounting)
```

All of this happens in one Odoo database, triggered by one user action.

## 1.3 Odoo's Technical Identity

| Layer | Technology |
|---|---|
| Backend / ORM | Python 3.10+ |
| Web Framework | Werkzeug (WSGI) |
| Database | PostgreSQL 14+ |
| Frontend (Classic) | Owl.js + XML QWeb templates |
| Frontend (Website) | QWeb server-side rendering |
| Communication | JSON-RPC, XML-RPC, REST (v17+) |
| Task Queue | Built-in ir.cron (no Celery) |
| Asset Bundling | Custom asset bundle system |

## 1.4 Odoo Editions

| Edition | License | Notes |
|---|---|---|
| Community | LGPL-3 | Free, open-source, full backend access |
| Enterprise | Proprietary | Adds advanced modules, requires subscription |

The entire backend ORM and framework is in Community. Enterprise adds modules on top.

## 1.5 Key Source Repositories

```
https://github.com/odoo/odoo          # Community
https://github.com/odoo/enterprise    # Enterprise (private)
```

The ORM core lives in: `odoo/odoo/models.py` (~5,000 lines)

## 1.6 Chapter Summary

- Odoo is a Python-based ERP with a modular architecture
- It integrates business functions via a shared PostgreSQL database
- The backend is open-source (LGPL), the frontend is built on Owl.js
- Enterprise adds modules but shares the same ORM and framework

## 1.7 Interview Questions

**Q1: What makes Odoo an ERP vs a simple web application?**
> ERP integrates multiple business processes (Sales, Inventory, Accounting, HR) into a single unified database and workflow engine. Odoo achieves this through module dependencies and shared data models (e.g., `res.partner` is used by CRM, Accounting, and HR simultaneously).

**Q2: What database does Odoo use and why?**
> PostgreSQL. Odoo's ORM generates DDL and DML specifically for PostgreSQL, relying on its advanced features: row-level security (used by record rules), JSON fields, full-text search via `tsvector`, and `RETURNING` clauses for batch inserts.

**Q3: What Python web framework does Odoo use?**
> Odoo uses Werkzeug as its WSGI adapter, but implements its own routing and controller layer on top (`odoo/http.py`). It does NOT use Django or Flask.

---

# CHAPTER 2: HIGH-LEVEL ARCHITECTURE

## 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│   Browser (Owl.js SPA)  │  Mobile App  │  External API Client  │
└────────────┬────────────┴──────┬────────┴──────────┬────────────┘
             │  HTTP/HTTPS       │                   │
             ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ODOO SERVER PROCESS                         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               HTTP Layer (Werkzeug WSGI)                 │   │
│  │         odoo/http.py  ←  Route dispatch                  │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                               │                                 │
│  ┌────────────────────────────▼────────────────────────────┐   │
│  │              Controller Layer                            │   │
│  │  web/controllers/main.py  │  module/controllers/*.py    │   │
│  │  @http.route decorators handle JSON-RPC / HTTP calls    │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                               │                                 │
│  ┌────────────────────────────▼────────────────────────────┐   │
│  │              Service / Business Logic Layer             │   │
│  │          model methods, wizard logic, workflows         │   │
│  └───────────────────────────┬─────────────────────────────┘   │
│                               │                                 │
│  ┌────────────────────────────▼────────────────────────────┐   │
│  │                     ORM Layer                           │   │
│  │              odoo/models.py  (~5,000 lines)             │   │
│  │   BaseModel  →  Model  →  TransientModel  →  AbstractModel  │
│  └───────────────────────────┬─────────────────────────────┘   │
│                               │                                 │
│  ┌────────────────────────────▼────────────────────────────┐   │
│  │            Database Abstraction (odoo/sql_db.py)        │   │
│  │       Connection pooling, cursor management             │   │
│  └───────────────────────────┬─────────────────────────────┘   │
└───────────────────────────────┼─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                         │
│   res_partner │ sale_order │ account_move │ stock_move │ ...    │
└─────────────────────────────────────────────────────────────────┘
```

## 2.2 Frontend Architecture

The Odoo frontend (starting v15) uses **Owl.js** — Odoo's own reactive component framework (similar to Vue.js but proprietary).

```
Frontend Stack:
  ┌─────────────────────────────────────┐
  │  Owl.js Component Tree              │
  │  ┌──────────────────────────────┐   │
  │  │  WebClient (root)            │   │
  │  │  ├── ActionManager           │   │
  │  │  │   ├── ListView            │   │
  │  │  │   ├── FormView            │   │
  │  │  │   ├── KanbanView          │   │
  │  │  │   └── GraphView           │   │
  │  │  ├── Navbar                  │   │
  │  │  └── NotificationManager     │   │
  │  └──────────────────────────────┘   │
  │  XML Templates (QWeb)               │
  │  SCSS → CSS bundled assets          │
  └─────────────────────────────────────┘
```

Frontend communicates with backend exclusively via **JSON-RPC** calls to `/web/dataset/call_kw`.

## 2.3 The ORM — The Heart of Odoo

The ORM (Object-Relational Mapper) is the most critical component. It:

1. Maps Python class definitions to PostgreSQL table DDL
2. Translates Python method calls into SQL statements
3. Manages transactions, cache, and the Environment
4. Enforces security rules at query time
5. Handles computed fields, default values, and constraints

**Key ORM source files:**
```
odoo/models.py           # BaseModel, Model, TransientModel
odoo/fields.py           # All field types (Char, Integer, Many2one, etc.)
odoo/api.py              # @api.model, @api.depends, @api.constrains decorators
odoo/osv/expression.py   # Domain expression parser and SQL generator
odoo/sql_db.py           # Database connection pool and cursor
```

## 2.4 Module System

Odoo's functionality is entirely composed of modules. The framework itself (`odoo/`) is just the loader and ORM. Every business feature lives in a module.

```
Module dependency graph (simplified):
base
  └── mail
        └── web
              └── sale
                    └── sale_management
                          └── crm
                                └── crm_enterprise
```

When `sale` is installed, Odoo installs all its dependencies first (base → mail → web → sale). Each module can extend any model defined by any other module it depends on.

## 2.5 Multi-Database, Multi-Process Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Odoo Process Manager                       │
│                                                         │
│  Worker 1 (HTTP)  │  Worker 2 (HTTP)  │  Worker 3 (cron)│
│       │                   │                   │         │
│       └─────────────┬─────┘                   │         │
│                     │                          │         │
│              Connection Pool                   │         │
│           (odoo/sql_db.py)                     │         │
└─────────────────────┬──────────────────────────┘         
                      │                                    
              ┌───────┴────────┐                          
              │  PostgreSQL    │                          
              │  mycompany_db  │                          
              │  mycompany2_db │  ← Multi-tenant          
              └────────────────┘                          
```

Odoo is **multi-tenant**: one server process can serve multiple company databases. Each database is fully isolated.

## 2.6 Important Configuration Files

```
/etc/odoo/odoo.conf        # Main server configuration
~/.odoorc                  # Developer local config
```

Key config parameters:
```ini
[options]
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
addons_path = /odoo/addons,/odoo/enterprise,/my/custom/addons
admin_passwd = admin
workers = 4
limit_time_real = 120
```

## 2.7 Chapter Summary

- Odoo has a layered architecture: HTTP → Controller → Business Logic → ORM → PostgreSQL
- The ORM (`models.py`) is the central component — all database interaction goes through it
- Frontend uses Owl.js and communicates via JSON-RPC
- The module system allows extending any model from any other module
- Odoo is multi-tenant at the database level

## 2.8 Interview Questions

**Q1: What is the role of `odoo/models.py`?**
> It defines `BaseModel`, the base class for all Odoo models. It contains ~5,000 lines implementing ORM methods (create, write, search, browse, unlink), field resolution, computed field scheduling, cache management, and SQL query generation.

**Q2: How does Odoo handle multiple companies?**
> Each company gets its own PostgreSQL database. The Odoo server process manages a connection pool per database. Multi-company within a single database is handled via `res.company` records and `company_id` fields with record rules that filter by the current user's allowed companies.

---

# CHAPTER 3: COMPLETE REQUEST LIFECYCLE

## 3.1 Overview

Let's trace the complete journey of a user clicking "Create Sales Order" in the UI.

```
User clicks "New" → browser sends HTTP POST → Odoo routes it →
Controller receives → ORM.create() called → SQL INSERT executed →
Response returned → UI refreshes
```

## 3.2 Step-by-Step Sequence Diagram

```
Browser          HTTP Layer      Controller      ORM            PostgreSQL
   │                 │               │            │                 │
   │──POST /web/──── ►               │            │                 │
   │ dataset/call_kw │               │            │                 │
   │ {model: "sale.order",           │            │                 │
   │  method: "create",              │            │                 │
   │  args: [{name:"S001",...}]}     │            │                 │
   │                 │               │            │                 │
   │                 │──dispatch()──►│            │                 │
   │                 │               │            │                 │
   │                 │   (auth check, session, CSRF verified)       │
   │                 │               │            │                 │
   │                 │               │─call_kw()─►│                │
   │                 │               │            │                 │
   │                 │               │  (get model class from registry)
   │                 │               │            │                 │
   │                 │               │            │─BEGIN──────────►│
   │                 │               │            │                 │
   │                 │               │            │─(ACL check)─────►
   │                 │               │            │                 │
   │                 │               │            │─(compute defaults)
   │                 │               │            │                 │
   │                 │               │            │─INSERT INTO──── ►│
   │                 │               │            │  sale_order     │
   │                 │               │            │◄─RETURNING id───│
   │                 │               │            │                 │
   │                 │               │            │─(compute fields)│
   │                 │               │            │                 │
   │                 │               │            │─COMMIT──────────►
   │                 │               │            │                 │
   │                 │               │◄──record ID│                 │
   │                 │◄──JSON resp───│            │                 │
   │◄──HTTP 200──────│               │            │                 │
   │  {result: 42}   │               │            │                 │
```

## 3.3 HTTP Entry Point: `odoo/http.py`

```python
# odoo/http.py (simplified)
class Application:
    """WSGI application entry point"""
    
    def __call__(self, environ, start_response):
        httprequest = werkzeug.wrappers.Request(environ)
        request = Request(httprequest)
        
        # Set request on thread-local
        _request_stack.push(request)
        
        # Find matching route
        rule, args = self.get_db_router(request.db).bind_to_environ(environ).match()
        
        # Authenticate session
        request.session.check_security()
        
        # Dispatch to controller
        result = rule.endpoint(**args)
        
        return result(environ, start_response)
```

## 3.4 The `call_kw` Controller: The Main Gateway

```python
# odoo/addons/web/controllers/dataset.py
class DataSet(http.Controller):
    
    @http.route('/web/dataset/call_kw', type='json', auth='user')
    def call_kw(self, model, method, args, kwargs):
        """
        This is the universal gateway from frontend to Python backend.
        Every list view load, form save, button click goes through here.
        """
        return self._call_kw(model, method, args, kwargs)
    
    def _call_kw(self, model, method, args, kwargs):
        # Get the model class from the global registry
        Model = request.env[model]   # e.g., request.env['sale.order']
        
        # Security: check if method is exposed (not prefixed with _)
        check_method_name(method)
        
        # Call the method
        return getattr(Model, method)(*args, **kwargs)
```

## 3.5 The Environment: `request.env`

```python
# odoo/api.py
class Environment:
    """
    The Environment is the gateway to everything:
    - env.user       → current user (res.users record)
    - env.uid        → current user's ID (integer)
    - env.cr         → database cursor (psycopg2 cursor)
    - env.context    → dict of contextual info (lang, tz, active_id)
    - env['model']   → get recordset of a model
    - env.ref('xml.id') → get record by XML ID
    """
    
    def __init__(self, cr, uid, context):
        self.cr = cr          # psycopg2 cursor
        self.uid = uid        # int user ID
        self.context = context  # dict
        self._cache = {}      # field value cache
        self._protected = {}  # protected fields (no recompute)
```

## 3.6 ORM Method Dispatch

```python
# odoo/models.py (simplified)
class BaseModel:
    
    @classmethod
    def _browse(cls, env, ids):
        """Return a recordset for the given ids"""
        records = cls.__new__(cls)
        records.env = env
        records._ids = ids
        return records
    
    def create(self, vals_list):
        """
        1. Validate values
        2. Apply defaults
        3. Run _before_create hooks
        4. Generate SQL INSERT
        5. Update computed fields
        6. Run _after_create hooks
        7. Return recordset
        """
        # ... 200 lines of logic
        query = "INSERT INTO %s (%s) VALUES %s RETURNING id"
        self.env.cr.execute(query, params)
        ids = [row[0] for row in self.env.cr.fetchall()]
        return self.browse(ids)
```

## 3.7 SQL Generation

```python
# odoo/osv/expression.py
def get_sql_operator(operator):
    return {
        '=':  '=',
        '!=': '!=',
        '<':  '<',
        '>':  '>',
        'like':  'LIKE',
        'ilike': 'ILIKE',
        'in':    'IN',
        'not in': 'NOT IN',
    }[operator]

# A domain like [('state', '=', 'sale'), ('amount_total', '>', 1000)]
# Gets translated to:
# WHERE "sale_order"."state" = 'sale' AND "sale_order"."amount_total" > 1000
```

## 3.8 Transaction Management

Odoo uses **one transaction per HTTP request** by default.

```python
# odoo/service/model.py
def execute_cr(cr, uid, obj, method, *args, **kw):
    """Execute a model method within a managed transaction"""
    try:
        result = execute(cr, uid, obj, method, *args, **kw)
        cr.commit()      # Commit on success
        return result
    except Exception:
        cr.rollback()    # Rollback on any error
        raise
```

If any part of the request raises an exception, the entire transaction rolls back. This is why Odoo's operations are atomic at the request level.

## 3.9 Practical Example: Full Create Flow

```python
# What happens when you call:
order = env['sale.order'].create({
    'partner_id': 1,
    'order_line': [(0, 0, {
        'product_id': 5,
        'product_uom_qty': 3,
    })]
})

# Internally:
# 1. ORM validates partner_id is a valid res.partner ID
# 2. ORM fetches default values (company_id, pricelist_id, etc.)
# 3. ORM checks ACL: does current user have create access on sale.order?
# 4. SQL: INSERT INTO sale_order (partner_id, company_id, state, ...) 
#         VALUES (1, 1, 'draft', ...) RETURNING id;
# 5. ORM processes order_line: [(0, 0, {...})] means "create new line"
# 6. SQL: INSERT INTO sale_order_line (order_id, product_id, product_uom_qty, ...)
#         VALUES (42, 5, 3, ...) RETURNING id;
# 7. Computed fields triggered: price_unit, price_subtotal, amount_total
# 8. SQL: UPDATE sale_order SET amount_total = 150.00 WHERE id = 42;
# 9. COMMIT
# 10. Return: sale.order(42,) recordset
```

## 3.10 Chapter Summary

- Every frontend action maps to a JSON-RPC POST to `/web/dataset/call_kw`
- The controller resolves the model from `request.env` registry
- The ORM executes validation, default injection, ACL checks, and SQL
- Transactions are automatic: commit on success, rollback on error
- The `Environment` (env) carries user, database cursor, and context

## 3.11 Interview Questions

**Q1: Where does every frontend-to-backend call land in Odoo?**
> `/web/dataset/call_kw` in `odoo/addons/web/controllers/dataset.py`. It dispatches to the appropriate model method using `request.env[model_name].method_name()`.

**Q2: How does Odoo ensure atomicity of operations?**
> Each HTTP request runs within a single PostgreSQL transaction. The transaction is committed only if the entire request succeeds. Any unhandled exception triggers `cr.rollback()`, undoing all changes made during that request.

**Q3: What is `self.env` and what does it contain?**
> `self.env` is an `Environment` object containing `cr` (database cursor), `uid` (current user ID), and `context` (dict with language, timezone, etc.). It also provides access to any model via `self.env['model.name']`.

---

# CHAPTER 4: PROJECT STRUCTURE AND MODULE ARCHITECTURE

## 4.1 Top-Level Directory Structure

```
odoo/                            # Root of Odoo community
├── odoo/                        # Core framework (NOT a module)
│   ├── __init__.py
│   ├── api.py                   # Decorators: @api.model, @api.depends
│   ├── exceptions.py            # UserError, AccessError, ValidationError
│   ├── fields.py                # All field types
│   ├── http.py                  # WSGI app, routing, Request
│   ├── models.py                # BaseModel, ORM
│   ├── modules/                 # Module loader
│   │   ├── graph.py             # Dependency graph
│   │   ├── loading.py           # Module installation
│   │   └── registry.py          # Model registry
│   ├── osv/
│   │   └── expression.py        # Domain → SQL converter
│   ├── service/
│   │   ├── model.py             # RPC service layer
│   │   └── server.py            # Worker process management
│   ├── sql_db.py                # DB connection pool
│   └── tools/                   # Utilities, config, misc
│
├── addons/                      # Built-in modules
│   ├── base/                    # The foundation module
│   ├── mail/                    # Chatter, messaging
│   ├── web/                     # Frontend framework
│   ├── sale/                    # Sales module
│   ├── account/                 # Accounting module
│   ├── stock/                   # Inventory module
│   ├── purchase/                # Purchase module
│   ├── mrp/                     # Manufacturing
│   └── hr/                      # Human Resources
│
├── setup.py
├── odoo-bin                     # CLI entry point
└── requirements.txt
```

## 4.2 Anatomy of an Odoo Module

Every module follows this exact structure:

```
my_module/
├── __init__.py                  # Import models/, wizards/, controllers/
├── __manifest__.py              # Module metadata (REQUIRED)
│
├── models/                      # Business logic
│   ├── __init__.py              # Import all model files
│   ├── sale_order.py            # Model extension or definition
│   └── res_partner.py
│
├── views/                       # XML: form/list/kanban views, menus
│   ├── sale_order_views.xml
│   └── menus.xml
│
├── security/                    # Access control
│   ├── ir.model.access.csv      # ACL rules
│   └── security.xml             # Record rules, groups
│
├── data/                        # Static data loaded on install
│   └── data.xml
│
├── demo/                        # Demo data (only in demo mode)
│   └── demo.xml
│
├── wizards/                     # TransientModel wizards
│   ├── __init__.py
│   └── my_wizard.py
│
├── controllers/                 # HTTP route handlers
│   ├── __init__.py
│   └── main.py
│
├── static/                      # Frontend assets
│   ├── src/
│   │   ├── js/
│   │   ├── css/
│   │   └── xml/                 # QWeb templates
│   └── description/
│       └── icon.png             # Module icon (shown in Apps list)
│
├── report/                      # PDF report templates
│   ├── report_views.xml
│   └── report_templates.xml
│
└── tests/                       # Automated tests
    ├── __init__.py
    └── test_sale_order.py
```

## 4.3 The `__manifest__.py` File

This is the module's passport. Odoo reads it to determine dependencies and features.

```python
# my_module/__manifest__.py
{
    'name': 'My Custom Module',
    'version': '16.0.1.0.0',         # Odoo version . Module version
    'category': 'Sales/CRM',
    'summary': 'Short description shown in Apps list',
    'description': """
        Long description in RST format.
    """,
    'author': 'Your Name / Company',
    'website': 'https://yoursite.com',
    
    # Dependencies: these modules MUST be installed first
    'depends': ['sale', 'mail', 'account'],
    
    # Files loaded in ORDER when module is installed/updated
    'data': [
        'security/security.xml',         # Load security groups first
        'security/ir.model.access.csv',  # Then ACLs
        'data/data.xml',                 # Then static data
        'views/my_views.xml',            # Then views
        'views/menus.xml',               # Menus last
    ],
    
    # Only loaded when server started with --load-demo-data
    'demo': [
        'demo/demo.xml',
    ],
    
    # Whether shown in Apps menu
    'application': True,
    
    # Whether it's installable
    'installable': True,
    
    # Whether auto-installed when all depends are present
    'auto_install': False,
    
    # License type
    'license': 'LGPL-3',
}
```

## 4.4 The `base` Module: Foundation of Everything

```
addons/base/
├── models/
│   ├── res_partner.py       # Contacts (res.partner) — used EVERYWHERE
│   ├── res_users.py         # Users (res.users) — authentication
│   ├── res_company.py       # Companies (res.company) — multi-company
│   ├── ir_model.py          # ir.model — the meta-model (models about models)
│   ├── ir_fields.py         # ir.model.fields — field definitions
│   ├── ir_rule.py           # ir.rule — record rules
│   ├── ir_actions.py        # ir.actions.* — window/server/URL actions
│   ├── ir_ui_menu.py        # ir.ui.menu — menu items
│   ├── ir_ui_view.py        # ir.ui.view — view definitions
│   └── ir_sequence.py       # ir.sequence — auto-increment sequences
```

The `ir_` prefix stands for **Internal Resource** — Odoo's meta-layer for storing system configuration.

## 4.5 Module Loading Sequence

```
python odoo-bin --addons-path=addons -d mydb -u my_module

Loading sequence:
1. Read __manifest__.py → get depends list
2. Topological sort of depends graph
3. For each module in sorted order:
   a. Import Python files (execute model class definitions)
   b. Register models in the global registry (odoo/modules/registry.py)
   c. Finalize ORM: resolve inheritance, compute field list
   d. Run ORM._auto_init(): CREATE TABLE / ALTER TABLE
   e. Load XML/CSV data files in manifest order
   f. Mark module as 'installed' in ir.module.module table
```

## 4.6 The Module Registry

```python
# odoo/modules/registry.py
class Registry:
    """
    Maps model names to their class.
    One registry per database.
    """
    
    def __init__(self, db_name):
        self.db_name = db_name
        self.models = {}       # {'sale.order': <class SaleOrder>, ...}
        self._init_modules()
    
    def __getitem__(self, model_name):
        return self.models[model_name]
    
    # Usage:
    # env['sale.order']  → calls registry['sale.order']
    # Returns the model class, which creates a recordset with env bound
```

## 4.7 Practical Example: Module for Custom Field on Sale Order

```
custom_sale_field/
├── __init__.py
├── __manifest__.py       # depends: ['sale']
├── models/
│   ├── __init__.py       # from . import sale_order
│   └── sale_order.py     # Extend sale.order with a new field
├── views/
│   └── sale_order_views.xml   # Add field to the form view
└── security/
    └── ir.model.access.csv    # Grant access (usually inherited)
```

```python
# custom_sale_field/models/__init__.py
from . import sale_order

# custom_sale_field/models/sale_order.py
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'    # Extend existing model
    
    custom_reference = fields.Char(
        string='Custom Reference',
        help='Internal tracking reference'
    )
```

```xml
<!-- custom_sale_field/views/sale_order_views.xml -->
<odoo>
  <record id="view_order_form_custom" model="ir.ui.view">
    <field name="name">sale.order.form.custom</field>
    <field name="model">sale.order</field>
    <field name="inherit_id" ref="sale.view_order_form"/>
    <field name="arch" type="xml">
      <xpath expr="//field[@name='client_order_ref']" position="after">
        <field name="custom_reference"/>
      </xpath>
    </field>
  </record>
</odoo>
```

## 4.8 Chapter Summary

- Every Odoo feature lives in a module with a strict directory convention
- `__manifest__.py` declares dependencies and file loading order
- The `base` module provides all fundamental meta-models (`ir.*`, `res.*`)
- The Registry maps model names to Python classes, one per database
- Module loading is: import Python → register models → sync DB schema → load XML data

## 4.9 Interview Questions

**Q1: What is the difference between `data/` and `demo/` in a module?**
> `data/` contains records loaded on every install (required configuration). `demo/` is loaded only when the server runs with `--load-demo-data` or the database is created in demo mode. Demo data is for development/testing only.

**Q2: What must come first in the `data` list in `__manifest__.py` and why?**
> Security files (`security/security.xml` for groups, `security/ir.model.access.csv` for ACLs) must be loaded first. Views and menus reference security groups, and records created during data loading need ACL rules to be in place. Loading views before ACLs causes integrity errors.

**Q3: What is the `ir.module.module` table?**
> It's the database table tracking all installed modules, their state (`installed`, `uninstalled`, `to upgrade`, `to remove`), and metadata. Odoo reads this on startup to know which modules are active.

---

# CHAPTER 5: PYTHON BACKEND INTERNALS

## 5.1 Models: The Core Abstraction

A **Model** in Odoo is a Python class that:
1. Declares fields (which become table columns)
2. Defines business methods
3. Maps to exactly one PostgreSQL table (for `models.Model`)

### 5.1.1 The Three Model Types

```python
from odoo import models

# TYPE 1: Persistent model → maps to a database table
class SaleOrder(models.Model):
    _name = 'sale.order'           # Table: sale_order
    _description = 'Sales Order'
    
    # ... fields and methods

# TYPE 2: Transient model → temporary, stored in DB, auto-vacuumed
# Used for wizards (dialogs)
class SaleOrderConfirm(models.TransientModel):
    _name = 'sale.order.confirm'   # Table: sale_order_confirm (temp)
    _description = 'Confirm Sale Order Wizard'

# TYPE 3: Abstract model → no table, used for mixins
class MailThread(models.AbstractModel):
    _name = 'mail.thread'          # No table created
    _description = 'Email Thread'
    # Provides chatter functionality to any model that inherits it
```

### 5.1.2 Model Attributes (`_` prefixed)

```python
class SaleOrder(models.Model):
    _name = 'sale.order'              # REQUIRED for new models. Table name = sale_order
    _description = 'Sales Order'     # Human-readable description
    _inherit = 'sale.order'          # Inherit/extend existing model
    _inherits = {'res.partner': 'partner_id'}  # Delegation inheritance
    
    _table = 'sale_order'            # Override table name (auto-derived from _name)
    _order = 'date_order desc, id'   # Default ORDER BY
    _rec_name = 'name'               # Field used for display name (name_get)
    _log_access = True               # Auto-add write_date, create_date columns
    
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name, company_id)', 
         'Order reference must be unique per company!'),
    ]
```

## 5.2 Fields: Column Definitions

Fields are Python class attributes that translate to PostgreSQL columns.

### 5.2.1 Basic Fields

```python
from odoo import models, fields

class ProjectTask(models.Model):
    _name = 'project.task'
    _description = 'Project Task'
    
    # ── STRING FIELDS ───────────────────────────────────────────
    name = fields.Char(
        string='Task Name',          # UI label (defaults to field name)
        required=True,               # NOT NULL constraint + UI validation
        size=256,                    # Max length (VARCHAR(256))
        index=True,                  # CREATE INDEX on this column
        translate=True,              # Enable multi-language translation
        default='New Task',
        copy=False,                  # Don't copy when duplicating record
        readonly=False,
        states={'done': [('readonly', True)]},  # Dynamic readonly by state
    )
    
    description = fields.Text(
        string='Description',        # TEXT column (no size limit)
    )
    
    notes = fields.Html(
        string='Notes',              # TEXT column, stored as HTML
        sanitize=True,               # Strip dangerous HTML on save
    )
    
    # ── NUMERIC FIELDS ──────────────────────────────────────────
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    
    hours_planned = fields.Float(
        string='Planned Hours',
        digits=(16, 2),              # Precision: 16 total digits, 2 decimal
    )
    
    budget = fields.Monetary(
        string='Budget',
        currency_field='currency_id', # Related field pointing to res.currency
    )
    
    # ── DATE/TIME FIELDS ────────────────────────────────────────
    date_start = fields.Date(
        string='Start Date',
    )
    
    date_deadline = fields.Datetime(
        string='Deadline',
        default=fields.Datetime.now,  # Callable default
    )
    
    # ── BOOLEAN ─────────────────────────────────────────────────
    is_closed = fields.Boolean(
        string='Closed',
        default=False,
    )
    
    # ── SELECTION ───────────────────────────────────────────────
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Very High'),
    ], string='Priority', default='0')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)  # tracking → log changes in chatter
    
    # ── BINARY ──────────────────────────────────────────────────
    attachment = fields.Binary(
        string='Attachment',
        attachment=True,   # Store in ir.attachment instead of column (recommended)
    )
    
    file_name = fields.Char('File Name')
```

### 5.2.2 Relational Fields

```python
class ProjectTask(models.Model):
    _name = 'project.task'
    
    # ── MANY2ONE: Foreign key ────────────────────────────────────
    # Many tasks belong to one project
    project_id = fields.Many2one(
        comodel_name='project.project',  # Target model
        string='Project',
        required=True,
        ondelete='cascade',   # CASCADE | SET NULL | RESTRICT | SET DEFAULT
        index=True,           # Always index Many2one fields!
        domain=[('active', '=', True)],  # Filter available choices in UI
    )
    
    # Many2one to res.users (common pattern)
    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        default=lambda self: self.env.user,  # Default to current user
    )
    
    # ── ONE2MANY: Inverse of Many2one ────────────────────────────
    # One task has many subtasks (if task has parent_id field)
    child_task_ids = fields.One2many(
        comodel_name='project.task',
        inverse_name='parent_id',    # The Many2one field on the other model
        string='Sub-tasks',
    )
    
    parent_id = fields.Many2one(
        'project.task',
        string='Parent Task',
        ondelete='cascade',
    )
    
    # ── MANY2MANY: Junction table ────────────────────────────────
    # Many tasks can have many tags
    tag_ids = fields.Many2many(
        comodel_name='project.tags',
        relation='project_task_tag_rel',   # Junction table name
        column1='task_id',                  # FK column for this model
        column2='tag_id',                   # FK column for the other model
        string='Tags',
    )
```

### 5.2.3 Computed Fields

```python
class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float('Quantity', default=1.0)
    price_unit = fields.Float('Unit Price')
    discount = fields.Float('Discount (%)')
    
    # Computed field — not stored in DB (computed on-the-fly)
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price_subtotal',  # Method that computes it
        store=True,       # If True: stored in DB (triggers SQL UPDATE on change)
                          # If False: computed every time it's accessed (default)
        digits=(16, 2),
    )
    
    @api.depends('product_uom_qty', 'price_unit', 'discount')
    def _compute_price_subtotal(self):
        """
        @api.depends declares which fields trigger recomputation.
        self is a RECORDSET — loop over it!
        """
        for line in self:
            price = line.price_unit * (1 - line.discount / 100)
            line.price_subtotal = price * line.product_uom_qty
    
    # Computed field with inverse (read/write)
    price_tax = fields.Float(
        compute='_compute_price_tax',
        inverse='_inverse_price_tax',  # Called when field is written
        store=False,
    )
    
    @api.depends('price_subtotal', 'tax_id')
    def _compute_price_tax(self):
        for line in self:
            taxes = line.tax_id.compute_all(line.price_subtotal)
            line.price_tax = taxes['total_included'] - taxes['total_excluded']
    
    def _inverse_price_tax(self):
        """Called when user writes to price_tax directly"""
        for line in self:
            # Back-calculate price_unit from the tax amount
            line.price_unit = line.price_tax / line.product_uom_qty
```

### 5.2.4 Related Fields

```python
class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    
    order_id = fields.Many2one('sale.order', string='Order')
    
    # Related field: traverse the relationship
    # Reads order_id.partner_id.name
    partner_name = fields.Char(
        related='order_id.partner_id.name',
        string='Customer Name',
        store=False,   # Only fetch from related model, don't store
        readonly=True,
    )
    
    # Related with store=True copies value to this table
    company_id = fields.Many2one(
        related='order_id.company_id',
        store=True,     # Stores a copy in sale_order_line.company_id
    )
```

## 5.3 Recordsets: The Central Data Structure

A **Recordset** is Odoo's equivalent of a queryset. It represents zero or more records of a model.

```python
# A recordset is created by:
order = env['sale.order'].browse(42)       # Specific record by ID
orders = env['sale.order'].browse([1,2,3]) # Multiple records
all_orders = env['sale.order'].search([])  # All records

# Type inspection
type(order)   # <class 'odoo.addons.sale.models.sale_order.SaleOrder'>
order._ids    # (42,) — tuple of database IDs
len(order)    # 1
bool(order)   # True if non-empty, False if empty

# Recordset is iterable
for o in orders:
    print(o.name)   # Access field on single record

# Recordset operations
r1 | r2    # Union (unique records)
r1 & r2    # Intersection
r1 - r2    # Difference
r1 + r2    # Concatenation (may have duplicates)
r1 == r2   # Same records?
record in recordset   # Membership test

# Recordset slicing
orders[0]    # First record
orders[:5]   # First 5 records
orders[-1]   # Last record

# Accessing fields
order.name           # String value
order.partner_id     # Returns a Many2one recordset (res.partner)
order.partner_id.name  # Access field on related record (follows FK)
order.order_line     # Returns One2many recordset
```

### 5.3.1 Recordset Methods

```python
# Existence check
if not order.exists():
    raise UserError("Record was deleted")

# Ensure singleton
order.ensure_one()   # Raises ValueError if len != 1

# Filtering (in-memory, no SQL)
draft_orders = orders.filtered(lambda o: o.state == 'draft')
draft_orders = orders.filtered('state')   # Filter truthy values

# Mapping (like Python map)
names = orders.mapped('name')               # Returns list of strings
partners = orders.mapped('partner_id')      # Returns recordset

# Sorting (in-memory)
sorted_orders = orders.sorted('date_order')
sorted_orders = orders.sorted('date_order', reverse=True)
sorted_orders = orders.sorted(key=lambda o: o.amount_total, reverse=True)
```

## 5.4 The Environment: `self.env`

```python
class SaleOrder(models.Model):
    _name = 'sale.order'
    
    def demonstrate_env(self):
        # ── BASIC ENV ACCESS ────────────────────────────────────
        user = self.env.user           # res.users record
        uid = self.env.uid             # int
        company = self.env.company     # res.company record
        companies = self.env.companies # All allowed companies (recordset)
        lang = self.env.lang           # 'en_US', 'fr_FR', etc.
        cr = self.env.cr               # psycopg2 cursor
        context = self.env.context    # dict
        
        # ── ACCESSING MODELS ─────────────────────────────────────
        Partner = self.env['res.partner']
        partner = Partner.browse(1)
        
        # ── env.ref() — Get record by XML ID ─────────────────────
        admin_group = self.env.ref('base.group_system')
        sale_team = self.env.ref('sales_team.crm_team_1')
        
        # ── ENVIRONMENT MODIFICATION ─────────────────────────────
        # sudo(): bypass access rights (use with caution!)
        all_orders = self.env['sale.order'].sudo().search([])
        
        # with_user(uid): run as different user
        other_env = self.env.with_user(5)
        
        # with_context(): add context keys
        ctx_env = self.env.with_context(lang='fr_FR', no_recompute=True)
        
        # with_company(): switch active company
        comp_env = self.env.with_company(other_company_id)
        
        # These chain: sudo().with_context(lang='fr_FR')
        
        # ── CONTEXT KEYS COMMONLY USED ────────────────────────────
        ctx = self.env.context
        lang = ctx.get('lang', 'en_US')
        tz = ctx.get('tz', 'UTC')
        active_id = ctx.get('active_id')   # ID of the record that opened a wizard
        active_ids = ctx.get('active_ids') # List of selected record IDs
        
        # ── CREATING ENV IN CRON / TESTS ─────────────────────────
        # In automated tests or cron jobs, you build env manually:
        from odoo.api import Environment
        with self.env.cr.savepoint():
            test_env = Environment(self.env.cr, user_id, {})
```

## 5.5 ORM: CRUD Operations

### 5.5.1 CREATE

```python
# Single record
order = self.env['sale.order'].create({
    'partner_id': partner.id,         # Many2one: pass integer ID
    'date_order': fields.Datetime.now(),
    'state': 'draft',
    'order_line': [
        # (0, 0, values_dict): Create and link new record
        (0, 0, {'product_id': product.id, 'product_uom_qty': 2}),
        # (4, id, False): Link existing record
        (4, existing_line_id, False),
    ],
})

# Batch create (much faster — single INSERT with multiple VALUES)
orders = self.env['sale.order'].create([
    {'partner_id': 1, 'date_order': '2024-01-01'},
    {'partner_id': 2, 'date_order': '2024-01-02'},
    {'partner_id': 3, 'date_order': '2024-01-03'},
])
# Generates: INSERT INTO sale_order (...) VALUES (...),(...),...  RETURNING id

# Generated SQL:
# INSERT INTO sale_order 
#   (partner_id, date_order, state, company_id, user_id, ...)
#   VALUES (1, '2024-01-01', 'draft', 1, 2, ...)
#   RETURNING id;
```

### 5.5.2 READ / SEARCH

```python
# ── BROWSE: by ID (no SQL until field access) ──────────────────
order = self.env['sale.order'].browse(42)
# No SQL yet — just wraps ID in recordset

# Field access triggers SQL:
print(order.name)
# SELECT "sale_order"."name" FROM "sale_order" WHERE id IN (42)

# ── SEARCH: domain filter ───────────────────────────────────────
# Domain syntax: [(field, operator, value), ...]
# Operators: = != < > <= >= like ilike in not in child_of parent_of

orders = self.env['sale.order'].search([
    ('state', '=', 'sale'),
    ('amount_total', '>', 1000),
    ('partner_id.country_id.code', '=', 'US'),
])
# SQL: SELECT id FROM sale_order 
#      JOIN res_partner ON ...
#      JOIN res_country ON ...
#      WHERE sale_order.state = 'sale'
#        AND sale_order.amount_total > 1000
#        AND res_country.code = 'US'

# Domain with OR:
domain = ['|', ('state', '=', 'sale'), ('state', '=', 'done')]
# SQL: WHERE state = 'sale' OR state = 'done'

# Domain with NOT:
domain = ['!', ('state', '=', 'cancelled')]
# SQL: WHERE NOT (state = 'cancelled')

# Complex: (A AND B) OR C
domain = ['|', '&', ('state','=','sale'), ('amount_total','>',1000), ('state','=','done')]

# Search with limit and order
orders = self.env['sale.order'].search(
    [('state', '=', 'sale')],
    limit=10,
    offset=0,
    order='date_order desc',
)

# ── SEARCH_COUNT: count without fetching ────────────────────────
count = self.env['sale.order'].search_count([('state', '=', 'sale')])

# ── READ: fetch specific fields (faster than accessing all) ─────
data = self.env['sale.order'].search_read(
    domain=[('state', '=', 'sale')],
    fields=['name', 'partner_id', 'amount_total'],
    limit=50,
)
# Returns: [{'id': 1, 'name': 'S001', 'partner_id': (5, 'ACME'), ...}, ...]
# Note: Many2one returns a tuple (id, display_name)

# ── READ on recordset ────────────────────────────────────────────
records = orders.read(['name', 'amount_total'])
```

### 5.5.3 WRITE (UPDATE)

```python
# Write on a recordset (all records get updated)
orders.write({
    'state': 'sale',
    'user_id': self.env.uid,
})
# SQL: UPDATE sale_order SET state = 'sale', user_id = 3 
#      WHERE id IN (1, 2, 3)

# Write with relational field commands:
order.write({
    'order_line': [
        (0, 0, {'product_id': 5, 'product_uom_qty': 1}),  # Create new line
        (1, 23, {'product_uom_qty': 5}),   # Update line with id=23
        (2, 24, False),                    # Delete line with id=24 (unlink)
        (3, 25, False),                    # Unlink (remove from order, keep record)
        (4, 26, False),                    # Link existing line id=26
        (5, False, False),                 # Unlink all lines
        (6, False, [27, 28]),             # Replace all lines with these ids
    ],
})
```

**The Magic Number Codes for Relational Fields (X2many):**

| Code | Name | Effect |
|---|---|---|
| (0, 0, vals) | CREATE | Creates a new linked record |
| (1, id, vals) | UPDATE | Updates the linked record |
| (2, id, False) | DELETE | Deletes the linked record |
| (3, id, False) | UNLINK | Removes the link (not the record) |
| (4, id, False) | LINK | Adds an existing record to the set |
| (5, False, False) | UNLINK ALL | Removes all links |
| (6, False, [ids]) | REPLACE | Replaces entire set with given IDs |

### 5.5.4 DELETE (UNLINK)

```python
# Delete records
orders.unlink()
# SQL: DELETE FROM sale_order WHERE id IN (1, 2, 3)
#      (Cascade deletes handled by PostgreSQL FK constraints)

# Safe deletion with check
if orders.filtered(lambda o: o.state in ('draft', 'cancelled')):
    safe = orders.filtered(lambda o: o.state in ('draft', 'cancelled'))
    safe.unlink()
else:
    raise UserError("Can only delete draft or cancelled orders")
```

## 5.6 Inheritance: Three Types

### 5.6.1 Classical Inheritance (`_inherit` = same `_name`)

```python
# EXTEND an existing model (most common pattern)
# Module: sale_custom adds a field to sale.order
class SaleOrder(models.Model):
    _inherit = 'sale.order'   # Extend existing model
    # No _name specified → same model, same table, just adds columns/methods
    
    custom_ref = fields.Char('Custom Reference')
    
    def action_confirm(self):
        """Override existing method"""
        # Call super() to run the original logic first
        result = super().action_confirm()
        # Add custom logic after
        self.send_custom_notification()
        return result
    
    def send_custom_notification(self):
        """New method added by this module"""
        for order in self:
            order.message_post(body=f"Order {order.name} confirmed")

# Effect on DB: ALTER TABLE sale_order ADD COLUMN custom_ref VARCHAR;
```

### 5.6.2 Prototypal Inheritance (`_inherit`, new `_name`)

```python
# COPY functionality into a new model
# Used to create a new model that starts with another's fields

class SaleOrderArchive(models.Model):
    _name = 'sale.order.archive'        # New model → new table
    _inherit = 'sale.order'             # Copy all fields and methods
    _description = 'Archived Sales Order'
    
    # Now sale.order.archive has ALL fields from sale.order
    # Plus any new fields you add here
    archive_date = fields.Date('Archive Date')
    archive_reason = fields.Text('Reason')
```

### 5.6.3 Delegation Inheritance (`_inherits`)

```python
# Delegate fields to a parent model via a Many2one
# The child stores its data in the parent's table

class Employee(models.Model):
    _name = 'hr.employee'
    _inherits = {'res.partner': 'address_id'}
    # Delegates: name, email, phone, street, city, etc. to res.partner
    
    address_id = fields.Many2one(
        'res.partner',
        required=True,
        ondelete='cascade',
    )
    
    # Employee-specific fields stored in hr_employee table
    department_id = fields.Many2one('hr.department')
    job_id = fields.Many2one('hr.job')
    
    # Access delegated fields transparently:
    # employee.name     → reads res_partner.name (no JOIN needed in Python)
    # employee.email    → reads res_partner.email
```

### 5.6.4 Mixin via AbstractModel

```python
# AbstractModel: no table, just a reusable mixin
class MailThread(models.AbstractModel):
    _name = 'mail.thread'
    
    message_ids = fields.One2many('mail.message', 'res_id', ...)
    
    def message_post(self, body, ...):
        """Post a message to the chatter"""
        ...

# Usage: inherit mail.thread in any persistent model
class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Multiple mixins
    
    # Now sale.order has message_ids, activity_ids, message_post(), etc.
```

## 5.7 Business Logic

### 5.7.1 Constraints

```python
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _name = 'sale.order'
    
    name = fields.Char('Reference', required=True)
    amount_total = fields.Float('Total')
    date_order = fields.Datetime('Order Date')
    date_delivery = fields.Datetime('Delivery Date')
    
    # SQL constraint (enforced at DB level — very fast)
    _sql_constraints = [
        ('name_company_unique', 
         'UNIQUE(name, company_id)',
         'Order reference must be unique per company!'),
         
        ('check_amount_positive',
         'CHECK(amount_total >= 0)',
         'Order total must be non-negative!'),
    ]
    
    # Python constraint (more flexible but slower)
    @api.constrains('date_order', 'date_delivery')
    def _check_dates(self):
        for order in self:
            if order.date_delivery and order.date_order:
                if order.date_delivery < order.date_order:
                    raise ValidationError(
                        f"Delivery date ({order.date_delivery}) cannot be "
                        f"before order date ({order.date_order})!"
                    )
```

### 5.7.2 Onchange Methods

```python
class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    
    product_id = fields.Many2one('product.product', string='Product')
    price_unit = fields.Float('Unit Price')
    name = fields.Text('Description')
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Called ONLY in UI, NOT during ORM write.
        Used to auto-fill fields when product is selected.
        Changes are NOT committed until user saves.
        """
        if self.product_id:
            self.name = self.product_id.get_product_multiline_description_sale()
            self.price_unit = self.product_id.lst_price
        else:
            self.name = ''
            self.price_unit = 0.0
        
        # Return a warning to the user (optional)
        if self.product_id and not self.product_id.active:
            return {
                'warning': {
                    'title': 'Archived Product',
                    'message': 'This product is archived. Consider using another.',
                }
            }
```

### 5.7.3 API Decorators

```python
from odoo import models, fields, api

class SaleOrder(models.Model):
    _name = 'sale.order'
    
    # @api.model: method called on class (no record), like a classmethod
    # self.env is available, but self has no IDs
    @api.model
    def _default_warehouse_id(self):
        return self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        )
    
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        default=_default_warehouse_id,
    )
    
    # @api.depends: defines field dependencies for computed fields
    @api.depends('order_line.price_subtotal', 'order_line.price_tax')
    def _compute_amounts(self):
        for order in self:
            order.amount_untaxed = sum(order.order_line.mapped('price_subtotal'))
            order.amount_tax = sum(order.order_line.mapped('price_tax'))
            order.amount_total = order.amount_untaxed + order.amount_tax
    
    # @api.constrains: validation after write
    @api.constrains('partner_id', 'company_id')
    def _check_partner_company(self):
        for order in self:
            if order.partner_id.company_id and \
               order.partner_id.company_id != order.company_id:
                raise ValidationError("Partner belongs to a different company!")
    
    # @api.onchange: UI-only reactivity
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist
    
    # @api.model_create_multi: called during batch create
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.order')
        return super().create(vals_list)
    
    # Regular instance method (called on recordset)
    def action_confirm(self):
        """State machine transition"""
        for order in self:
            if order.state != 'draft':
                raise UserError("Only draft orders can be confirmed!")
            order.write({'state': 'sale'})
            order._create_picking()   # Trigger stock picking creation
        return True
    
    def _create_picking(self):
        """Private method (convention: prefix with _)"""
        for order in self:
            # Create stock picking for delivery
            picking = self.env['stock.picking'].create({
                'partner_id': order.partner_id.id,
                'origin': order.name,
                ...
            })
```

## 5.8 Chapter Summary

- Models are Python classes inheriting from `models.Model`, mapped to PostgreSQL tables
- Fields are class attributes that become columns; computed fields have no column (unless `store=True`)
- Recordsets are zero-or-more record containers — always iterate over them
- `self.env` gives access to user, cursor, context, and any model
- CRUD: `create(vals)`, `write(vals)`, `search(domain)`, `browse(ids)`, `unlink()`
- Three inheritance types: extension (`_inherit`), copy (`_name + _inherit`), delegation (`_inherits`)
- Business logic uses `@api.constrains`, `@api.onchange`, `@api.depends`
- X2many commands: 0=create, 1=update, 2=delete, 3=unlink, 4=link, 5=clear, 6=replace

## 5.9 Interview Questions

**Q1: What is the difference between `@api.model` and a regular method?**
> A regular method is called on a recordset (`self` has IDs). `@api.model` is called on the model class with an empty recordset (`self._ids == ()`). Use `@api.model` for factory methods, default value computations, and `_default_*` functions.

**Q2: What is the difference between `store=True` and `store=False` on a computed field?**
> `store=False` (default): the field is computed every time it's read — no DB column, always fresh but slower. `store=True`: a DB column is created, the field is computed and written to DB whenever its `@api.depends` fields change — faster to read but requires trigger-based updates.

**Q3: What does `self.env['res.partner'].sudo().search([])` do?**
> It accesses the `res.partner` model with superuser privileges (`sudo()`), bypassing access control rules, and searches all records. This is necessary when a regular user-level operation needs to read records they wouldn't otherwise have access to (e.g., reading partner data in a public website controller).

**Q4: What is the X2many command for replacing all existing lines with a new set?**
> `(6, False, [id1, id2, id3])` — command 6 replaces all linked records with the specified IDs.
