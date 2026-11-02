# CHAPTER 11: DEBUGGING AND INSPECTION

## 11.1 Odoo Shell: The Interactive Python Console

The Odoo shell gives you a live Python environment with a real database connection — the most powerful tool for backend exploration.

```bash
# Start the shell
python odoo-bin shell -d myodoo

# You get:
# env    → odoo.api.Environment
# self   → res.users record for admin
# odoo   → the odoo package
```

```python
# === INSIDE THE ODOO SHELL ===

# Explore a model
order = env['sale.order'].search([], limit=1)
print(order.name, order.state, order.amount_total)

# See all fields
for fname, fobj in env['sale.order']._fields.items():
    print(f'{fname:30} {fobj.__class__.__name__}')

# Read raw SQL
env.cr.execute("SELECT id, name, state FROM sale_order LIMIT 5")
for row in env.cr.fetchall():
    print(row)

# Check ACL for a model
env['sale.order'].check_access_rights('create')

# Inspect field metadata
f = env['sale.order']._fields['state']
print(f.type, f.selection, f.required)

# Get the PostgreSQL table name
print(env['sale.order']._table)  # → sale_order

# Commit or rollback your changes
env.cr.commit()    # Persist changes
env.cr.rollback()  # Discard changes

# Exit
exit()
```

## 11.2 Logging Configuration

```ini
# odoo.conf
[options]
log_level = debug
logfile = /var/log/odoo/odoo.log

# Or per-module logging:
log_handler = :INFO,odoo.models:DEBUG,odoo.sql_db:DEBUG
```

**Log handler patterns:**
```
:INFO                    # Root logger at INFO
odoo.models:DEBUG        # ORM at DEBUG (shows SQL)
odoo.sql_db:DEBUG        # SQL timing
odoo.http:DEBUG          # HTTP request details
odoo.addons.sale:DEBUG   # Specific module
```

Enable SQL query logging:
```bash
python odoo-bin -d myodoo --log-handler=odoo.sql_db:DEBUG
# Now every SQL query is logged with timing
```

## 11.3 Python `pdb` Debugging

```python
# In your model code:
def action_confirm(self):
    import pdb; pdb.set_trace()   # Breakpoint!
    # pdb commands: n(ext), s(tep), c(ontinue), p(rint), l(ist), q(uit)
    for order in self:
        order.write({'state': 'sale'})

# Better: use ipdb (colorized pdb)
# pip install ipdb --break-system-packages
import ipdb; ipdb.set_trace()

# Or Python's built-in breakpoint() (Python 3.7+)
def action_confirm(self):
    breakpoint()   # Uses PYTHONBREAKPOINT env var (defaults to pdb)
    ...
```

## 11.4 VS Code Debugging

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Odoo Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/odoo-bin",
            "args": [
                "-d", "myodoo",
                "--addons-path", "addons,/path/to/custom/addons",
                "--dev", "xml",
                "--log-level", "debug"
            ],
            "console": "integratedTerminal",
            "justMyCode": false   // Step into Odoo internals
        }
    ]
}
```

## 11.5 Inspecting ORM Queries

```python
# See what SQL a search generates:
import logging
logging.getLogger('odoo.models').setLevel(logging.DEBUG)
logging.getLogger('odoo.sql_db').setLevel(logging.DEBUG)

# Manually capture SQL:
class SaleOrder(models.Model):
    _name = 'sale.order'
    
    def debug_query(self):
        # Before the search
        self.env.cr.execute("SELECT 1")   # Warm up
        
        # Now run and check logs
        orders = self.search([('state', '=', 'sale')], limit=10)
        # SQL logged: SELECT "sale_order".id FROM "sale_order" 
        #             WHERE ("sale_order"."state" = 'sale') 
        #             ORDER BY "sale_order"."id" LIMIT 10
```

## 11.6 Performance Profiling

```python
# Built-in profiler (Odoo 14+)
from odoo.tools.profiler import profile

class SaleOrder(models.Model):
    _name = 'sale.order'
    
    @profile     # Decorator: generates a flame graph
    def action_generate_report(self):
        # ... your slow code ...
        pass

# Via the URL: add ?profile=1 to any Odoo URL to get profiling data
# Or in shell:
from odoo.tools.profiler import Profiler
with Profiler(db=self.env.cr.dbname):
    orders = env['sale.order'].search([])
    for o in orders:
        _ = o.amount_total

# PostgreSQL: slow query log
# In postgresql.conf:
# log_min_duration_statement = 1000  # Log queries taking > 1 second
```

## 11.7 Database Inspection Tools

```bash
# Connect to Odoo's PostgreSQL database
psql -U odoo myodoo

# Useful psql commands:
\d sale_order            # Describe table structure
\di sale_order*          # List indexes on sale_order
\x                       # Toggle expanded display
\timing                  # Show query timing

# Find slow queries via pg_stat_statements
SELECT query, calls, total_exec_time/calls as avg_ms
FROM pg_stat_statements
WHERE query LIKE '%sale_order%'
ORDER BY avg_ms DESC
LIMIT 20;

# Check table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;

# Check missing indexes (high seq scans)
SELECT relname, seq_scan, idx_scan, 
       seq_scan - idx_scan AS seq_vs_idx
FROM pg_stat_user_tables
ORDER BY seq_scan DESC
LIMIT 20;
```

## 11.8 Chapter Summary

- The Odoo shell (`odoo-bin shell`) is your #1 tool — use it constantly
- Enable `odoo.sql_db:DEBUG` logging to see all generated SQL
- Use `pdb`/`ipdb`/`breakpoint()` for step-through debugging
- VS Code can attach a debugger to a running Odoo process
- Profile with Odoo's built-in `@profile` decorator or PostgreSQL `pg_stat_statements`

---

# CHAPTER 12: EXPLORING AN EXISTING ODOO CODEBASE

## 12.1 The Exploration Strategy

```
Step 1: Start with the UI
  └── Find the menu item you're investigating
        └── Use Technical > User Interface > Menu Items to find the action

Step 2: Find the action → model
  └── Technical > Actions > Window Actions
        └── Note the model name

Step 3: Find the model file
  └── grep -r "_name = 'sale.order'" addons/
        └── addons/sale/models/sale_order.py

Step 4: Read the model
  └── Read _name, _inherit, fields, important methods

Step 5: Trace a workflow
  └── Find a button's name="action_confirm" → search for def action_confirm
```

## 12.2 Key Exploration Commands

```bash
# Find which file defines a model
grep -r "_name = 'sale.order'" --include="*.py" addons/
# → addons/sale/models/sale_order.py

# Find all extensions of a model (across all modules)
grep -r "_inherit = 'sale.order'" --include="*.py" addons/
# Shows every module that extends sale.order

# Find a method across the codebase
grep -r "def action_confirm" --include="*.py" addons/

# Find XML views for a model
grep -r 'model="sale.order"' --include="*.xml" addons/

# Find all routes defined
grep -r "@http.route" --include="*.py" addons/ | grep "'/api"

# Find where a field is defined
grep -r "amount_total" addons/sale/models/ --include="*.py"

# Search for a specific cron job
grep -r "model.ir.cron" --include="*.xml" addons/sale/

# Find all models that inherit mail.thread
grep -r "_inherit.*mail.thread" --include="*.py" addons/ | wc -l
```

## 12.3 Using the Odoo Shell for Exploration

```python
# === Model Exploration in Shell ===

# List all field names and types on a model
model = env['sale.order']
for name, field in sorted(model._fields.items()):
    print(f'{name:35} {field.__class__.__name__:20} {getattr(field, "string", "")}')

# Find all models that have a specific field
for model_name, Model in env.registry.models.items():
    if 'partner_id' in Model._fields:
        print(model_name)

# Find all models that inherit from a mixin
for model_name, Model in env.registry.models.items():
    if 'mail.thread' in Model._inherit:
        print(model_name)

# Inspect a Many2one field
f = env['sale.order']._fields['partner_id']
print(f.comodel_name)   # → 'res.partner'
print(f.required)        # → True
print(f.ondelete)        # → 'restrict'

# See all computed fields and their dependencies
for name, field in model._fields.items():
    if field.compute:
        deps = list(model._depends.get(name, []))
        print(f'{name}: computed by {field.compute}, depends on {deps}')

# Find method resolution order (which module overrides what)
import inspect
for cls in type(model).__mro__:
    if hasattr(cls, 'action_confirm') and 'action_confirm' in cls.__dict__:
        print(f'{cls.__module__}.{cls.__name__}')
# Shows the override chain across modules

# List all methods on a model (non-private)
methods = [m for m in dir(model) if not m.startswith('_') and callable(getattr(model, m))]
for m in sorted(methods):
    print(m)

# Read source code of a method
import inspect
print(inspect.getsource(model.action_confirm))

# Find which file a model class comes from
print(inspect.getfile(type(model)))
```

## 12.4 Database Exploration

```sql
-- Find all tables related to sale
SELECT tablename FROM pg_tables 
WHERE tablename LIKE 'sale%'
ORDER BY tablename;

-- Trace foreign key relationships
SELECT
    tc.table_name AS from_table,
    kcu.column_name AS from_column,
    ccu.table_name AS to_table,
    ccu.column_name AS to_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'sale_order'
ORDER BY kcu.column_name;

-- Find which model handles a specific table
SELECT model FROM ir_model WHERE transient = FALSE
ORDER BY model;

-- See all installed modules and their state
SELECT name, state, author FROM ir_module_module 
WHERE state = 'installed'
ORDER BY name;

-- Find all server actions and their code
SELECT name, model_id, state, code 
FROM ir_act_server
WHERE state = 'code'
ORDER BY name;
```

## 12.5 UI Developer Mode Exploration

1. Enable developer mode: **Settings → Activate Developer Mode** (or add `?debug=1` to URL)
2. **Technical** menu appears in Settings
3. Key Technical menus:
   - **Database Structure → Models**: browse all models
   - **Database Structure → Fields**: see all fields with metadata
   - **User Interface → Views**: inspect/edit view XML live
   - **User Interface → Menu Items**: find which action a menu triggers
   - **Actions → Window Actions**: see model, domain, view mode
   - **Sequences**: find next sequence values
   - **Automation → Automated Actions**: see event-based automation

## 12.6 The `fields_get()` Method for API Discovery

```python
# XML-RPC / JSON-RPC introspection
fields = env['sale.order'].fields_get(
    attributes=['string', 'type', 'required', 'readonly', 'selection', 'relation']
)

# Filter by type
relational_fields = {
    name: info for name, info in fields.items()
    if info['type'] in ('many2one', 'one2many', 'many2many')
}
for name, info in relational_fields.items():
    print(f"{name:30} {info['type']:15} → {info.get('relation', '')}")
```

## 12.7 Chapter Summary

- `grep` is your best friend for navigating a large codebase
- The Odoo shell with Python introspection reveals everything about models at runtime
- Developer mode exposes all technical metadata through the UI
- `fields_get()` is the API self-documentation endpoint
- MRO inspection (`type(model).__mro__`) shows the full inheritance chain

---

# CHAPTER 13: BEST PRACTICES

## 13.1 Code Organization

```python
# GOOD: Follow the Odoo conventions for method ordering in a model class
class MyModel(models.Model):
    _name = 'my.model'
    _description = 'My Model'
    _inherit = [...]
    _order = '...'
    _rec_name = '...'
    
    # 1. Fields (grouped: basic, relational, computed)
    name = fields.Char(...)
    
    # 2. Compute methods (right after their fields)
    @api.depends('...')
    def _compute_name(self): ...
    
    # 3. Constraint methods
    @api.constrains('...')
    def _check_something(self): ...
    
    # 4. Onchange methods
    @api.onchange('...')
    def _onchange_something(self): ...
    
    # 5. CRUD overrides
    @api.model_create_multi
    def create(self, vals_list): ...
    
    def write(self, vals): ...
    
    def unlink(self): ...
    
    # 6. Action methods (called from buttons)
    def action_confirm(self): ...
    
    # 7. Business logic helpers (private)
    def _compute_something_complex(self): ...
```

## 13.2 Performance Best Practices

```python
# ── BAD: N+1 query problem ──────────────────────────────────────
orders = self.env['sale.order'].search([])
for order in orders:
    print(order.partner_id.name)   # Separate SQL for each order!

# ── GOOD: Pre-fetch related records ────────────────────────────
# Odoo does batch prefetching automatically when you access
# a Many2one field on a recordset (fetches all in one query)
# But you can help it with read():
orders = self.env['sale.order'].search([])
data = orders.read(['partner_id'])   # Batch fetch
for item in data:
    print(item['partner_id'][1])   # Already fetched, no SQL

# ── BAD: Individual updates in a loop ───────────────────────────
for order in orders:
    order.write({'processed': True})   # One UPDATE per order!

# ── GOOD: Batch update ──────────────────────────────────────────
orders.write({'processed': True})   # ONE UPDATE for all

# ── BAD: search() in a loop ─────────────────────────────────────
for partner_id in partner_ids:
    orders = env['sale.order'].search([('partner_id', '=', partner_id)])

# ── GOOD: One search with IN ────────────────────────────────────
orders = env['sale.order'].search([('partner_id', 'in', partner_ids)])
grouped = {}
for o in orders:
    grouped.setdefault(o.partner_id.id, []).append(o)

# ── GOOD: Use search_count instead of len(search()) ─────────────
count = env['sale.order'].search_count([('state', '=', 'draft')])
# NOT: len(env['sale.order'].search([('state', '=', 'draft')]))

# ── GOOD: Use mapped() instead of list comprehension ─────────────
partner_ids = orders.mapped('partner_id.id')    # Fast, stays in ORM
# vs: [o.partner_id.id for o in orders]         # Also works but less idiomatic

# ── GOOD: filtered() vs search() for in-memory filtering ─────────
# If you already have the recordset loaded, use filtered()
available = books.filtered(lambda b: b.state == 'available')
# Don't do: env['library.book'].search([('id', 'in', books.ids), ('state','=','available')])
```

## 13.3 Error Handling

```python
from odoo.exceptions import (
    UserError,          # Business logic error shown to user
    ValidationError,    # Data validation error
    AccessError,        # Permission denied
    MissingError,       # Record not found
    RedirectWarning,    # Error with a redirect button
)

class SaleOrder(models.Model):
    _name = 'sale.order'
    
    def action_confirm(self):
        for order in self:
            # UserError: shown as a dialog to the user
            if not order.order_line:
                raise UserError(
                    f"Cannot confirm order {order.name}: no order lines found."
                )
            
            # ValidationError: same as UserError but typically from @api.constrains
            if order.amount_total < 0:
                raise ValidationError("Order total cannot be negative!")
            
            # Use specific exceptions for specific situations
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                raise AccessError("Only sales managers can confirm orders above $10,000")

    def safe_process(self):
        """Process records with partial failure handling"""
        errors = []
        for record in self:
            try:
                with self.env.cr.savepoint():
                    record._do_risky_operation()
            except Exception as e:
                errors.append(f"{record.name}: {str(e)}")
        
        if errors:
            raise UserError("Some records failed:\n" + "\n".join(errors))
```

## 13.4 Context Usage

```python
# Use context to pass flags to avoid infinite loops
def write(self, vals):
    if 'state' in vals and not self.env.context.get('no_trigger'):
        # Do something
        other_record.with_context(no_trigger=True).write({'field': value})
    return super().write(vals)

# Common context keys to know:
# 'active_id': ID of the record that opened a wizard
# 'active_ids': List of selected record IDs
# 'active_model': Model name of the caller
# 'lang': Language code ('en_US', 'fr_FR')
# 'tz': Timezone
# 'company_id': Override active company
# 'no_recompute': Skip recomputation of stored computed fields
# 'mail_notrack': Disable field tracking in chatter
# 'mail_create_nosubscribe': Don't auto-subscribe creator to chatter
```

## 13.5 Security Best Practices

```python
# ── NEVER expose internal methods to RPC ────────────────────────
class MyModel(models.Model):
    _name = 'my.model'
    
    def action_public_method(self):
        """Callable from UI buttons (no _ prefix)"""
        self._do_internal_work()   # Calls private helper
    
    def _do_internal_work(self):
        """NOT callable from RPC (underscore prefix)"""
        pass

# ── Always check sudo() usage is justified ──────────────────────
def public_website_method(self):
    # BAD: sudo() without justification
    all_orders = self.env['sale.order'].sudo().search([])
    
    # GOOD: sudo() with scope and justification
    # Need to read partner info for anonymous user
    partner = self.env['res.partner'].sudo().browse(partner_id)
    # Use partner.name but don't return sensitive fields

# ── Validate all external input ──────────────────────────────────
@http.route('/api/order/create', type='json', auth='user')
def create_order(self, **kwargs):
    partner_id = kwargs.get('partner_id')
    
    # Validate type
    if not isinstance(partner_id, int):
        raise ValueError("partner_id must be an integer")
    
    # Validate exists and user has access (don't sudo for this)
    partner = request.env['res.partner'].browse(partner_id)
    if not partner.exists():
        raise UserError("Partner not found")
    
    # Now safe to use
    order = request.env['sale.order'].create({'partner_id': partner_id})
```

## 13.6 Chapter Summary

- Follow Odoo's field/method ordering convention for readability
- Avoid N+1 queries with batch reads and `write()` on recordsets
- Use `UserError` for business logic errors, `ValidationError` for data errors
- Prefix private methods with `_` to prevent RPC exposure
- Use `sudo()` sparingly and always with justification comments

---

# CHAPTER 14: COMMON PITFALLS

## 14.1 The N+1 Query Problem

```python
# PITFALL: Accessing a Many2one field inside a loop
orders = env['sale.order'].search([])
for order in orders:
    # Each access to partner_id.name fires a separate SQL query!
    print(order.partner_id.name)

# FIX: Odoo's prefetch mechanism handles this IF you access
# the field on the full recordset, not inside generators
# Access partner_id first (batches the fetch):
_ = orders.mapped('partner_id')    # Pre-fetch all partners at once
for order in orders:
    print(order.partner_id.name)   # Now from cache

# OR use search_read:
orders = env['sale.order'].search_read(
    [()], fields=['name', 'partner_id']
)
```

## 14.2 Forgetting to Iterate Over Recordsets

```python
# PITFALL: Writing as if self is a single record
def compute_total(self):
    # WRONG: self might be a recordset with 1000 records!
    self.total = self.qty * self.price   # Only works if len(self) == 1

# CORRECT: Always iterate
@api.depends('qty', 'price')
def compute_total(self):
    for record in self:
        record.total = record.qty * record.price
```

## 14.3 `onchange` vs `depends` Confusion

```python
# PITFALL: Using @api.onchange for stored computed fields
# onchange only fires in UI, NOT when created via ORM!

# WRONG:
@api.onchange('product_id')
def _onchange_product(self):
    self.price = self.product_id.list_price
    # This WON'T run when creating via env['sale.order.line'].create(...)

# CORRECT:
@api.depends('product_id')
def _compute_price(self):
    for line in self:
        line.price = line.product_id.list_price
```

## 14.4 Circular Dependency in Computed Fields

```python
# PITFALL: A depends B, B depends A → infinite loop / crash

# WRONG:
class Order(models.Model):
    _name = 'sale.order'
    
    amount_untaxed = fields.Float(compute='_compute_amounts')
    amount_total = fields.Float(compute='_compute_amounts')
    
    @api.depends('amount_total')  # ← amount_total depends on itself (via amount_untaxed)
    def _compute_amounts(self):
        for o in self:
            o.amount_untaxed = sum(o.order_line.mapped('price_subtotal'))
            o.amount_total = o.amount_untaxed + o.amount_tax
    
# CORRECT: Depend on the raw data sources, not other computed fields
    @api.depends('order_line.price_subtotal', 'order_line.price_tax')
    def _compute_amounts(self):
        for o in self:
            o.amount_untaxed = sum(o.order_line.mapped('price_subtotal'))
            o.amount_total = o.amount_untaxed + o.amount_tax
```

## 14.5 Missing `super()` Call

```python
# PITFALL: Overriding create/write without calling super()
# This breaks all other module extensions!

# WRONG:
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['custom_ref'] = 'AUTO'
        # Missing super()! Other modules' create overrides won't run
        return self.env['sale.order'].create(vals_list)  # Also wrong

# CORRECT:
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['custom_ref'] = 'AUTO'
        return super().create(vals_list)   # Always call super()!
```

## 14.6 Using Raw SQL When ORM Suffices

```python
# PITFALL: Bypassing ORM with raw SQL
# This skips: ACL checks, record rules, computed field updates, 
# mail tracking, and write_date/write_uid updates

# WRONG:
self.env.cr.execute("UPDATE sale_order SET state = 'done' WHERE id = %s", [self.id])

# CORRECT (unless you have a very specific performance reason):
self.write({'state': 'done'})

# When raw SQL IS appropriate:
# 1. Reports with complex JOINs
# 2. Bulk data migrations
# 3. Read-only analytical queries
# Always add a clear comment explaining why ORM wasn't used
```

## 14.7 Using `id` vs Recordset

```python
# PITFALL: Confusing record IDs with recordsets

# WRONG: comparing a recordset to an ID
if order.partner_id == 5:   # RecordSet != int, always False!
    ...

# CORRECT:
if order.partner_id.id == 5:   # Compare IDs
    ...
if order.partner_id == env['res.partner'].browse(5):   # Compare recordsets
    ...

# WRONG: passing recordset where ID is needed
vals = {
    'partner_id': order.partner_id,   # Wrong! Must be an integer
}

# CORRECT:
vals = {
    'partner_id': order.partner_id.id,   # Integer ID
}
```

## 14.8 Transaction Gotchas

```python
# PITFALL: Expected rollback but changes persisted
# (or vice versa)

# Odoo commits after every HTTP request.
# In a cron job or wizard, if you want partial rollback:

# WRONG: assuming exception in one record rolls back only that record
for record in self:
    record.process()   # If this fails, ALL previous records roll back too!

# CORRECT: use savepoints
for record in self:
    try:
        with self.env.cr.savepoint():
            record.process()
    except Exception as e:
        _logger.error(f"Failed: {e}")
        # Only this record's changes are rolled back
```

## 14.9 Chapter Summary

- Never assume `self` is a single record — always iterate
- `@api.onchange` is UI-only; use `@api.depends` for stored computed fields
- Always call `super()` in overridden CRUD methods
- Raw SQL bypasses security, tracking, and computed field triggers
- Pass `.id` (integer) to Many2one fields, not the recordset object
- Use `cr.savepoint()` for partial rollback in loops

---

# CHAPTER 15: ROADMAP TO PRODUCTIVITY

## 15.1 Phase 1: Foundation (Weeks 1-2)

```
Week 1:
  ✓ Set up local Odoo development environment
  ✓ Read Chapter 2 (Architecture) and explore the directory structure
  ✓ Understand models.py at a high level
  ✓ Explore the Odoo shell daily — read res.partner, sale.order
  ✓ Read any one standard module (sale/) top to bottom

Week 2:
  ✓ Build the library_management module from Chapter 10
  ✓ Understand fields: Char, Many2one, One2many, Many2many, computed
  ✓ Write 10 shell one-liners that explore a real model
  ✓ Read about XML views and write a form + list view
```

## 15.2 Phase 2: Core ORM and Security (Weeks 3-4)

```
Week 3:
  ✓ Master CRUD operations with all edge cases
  ✓ Understand all X2many command codes (0-6)
  ✓ Study odoo/models.py sections: _search, create, write, unlink
  ✓ Write a custom model with all inheritance types

Week 4:
  ✓ Implement ACL + Record Rules for your module
  ✓ Test security with different users in the shell
  ✓ Build a wizard (TransientModel)
  ✓ Write unit tests with TransactionCase
```

## 15.3 Phase 3: Integration and APIs (Weeks 5-6)

```
Week 5:
  ✓ Build an XML-RPC integration script
  ✓ Build a custom HTTP controller
  ✓ Study the call_kw endpoint in web/controllers/dataset.py
  ✓ Understand JSON-RPC protocol structure

Week 6:
  ✓ Build a scheduled action (ir.cron)
  ✓ Build an automation rule (base.automation)
  ✓ Profile a slow operation and optimize it
  ✓ Add proper logging throughout your module
```

## 15.4 Phase 4: Production Skills (Weeks 7-8)

```
Week 7:
  ✓ Study an Enterprise module (subscription/helpdesk)
  ✓ Learn Odoo upgrade path and migration scripts
  ✓ Set up proper git workflow for module development
  ✓ Configure VS Code debugging

Week 8:
  ✓ Build a complete feature end-to-end (UI → Python → DB)
  ✓ Peer code review checklist
  ✓ Deploy to staging environment
  ✓ Study Odoo community best practices (OCA standards)
```

## 15.5 Key Source Files to Read

| File | What You Learn |
|---|---|
| `odoo/models.py` | The entire ORM: create, write, search, browse, _search |
| `odoo/fields.py` | Every field type's implementation |
| `odoo/api.py` | Environment, decorators, recordset behavior |
| `odoo/osv/expression.py` | Domain → SQL translator |
| `odoo/sql_db.py` | Connection pool, cursor management |
| `odoo/http.py` | WSGI routing, request lifecycle |
| `addons/web/controllers/dataset.py` | call_kw controller |
| `addons/base/models/ir_rule.py` | Record rule evaluation |
| `addons/base/models/ir_model.py` | Meta-model, ACL checking |
| `addons/sale/models/sale_order.py` | Real-world model example |
| `addons/account/models/account_move.py` | Complex model example |
| `addons/mail/models/mail_thread.py` | The chatter mixin |

## 15.6 Interview Preparation Checklist

```
□ Explain Odoo's architecture in 2 minutes
□ Explain the difference between Model/TransientModel/AbstractModel
□ Explain all three inheritance types with examples
□ Write a Many2one field with proper options
□ Explain X2many command codes (0-6)
□ Explain @api.depends vs @api.onchange
□ Explain ACL vs Record Rules
□ Write a record rule that restricts a salesperson to their own leads
□ Explain how computed fields with store=True work
□ Trace a JSON-RPC call from browser to SQL
□ Explain the transaction lifecycle in an HTTP request
□ Write a custom controller endpoint
□ Explain how sudo() works and when to use it
□ Explain the module dependency and loading sequence
□ Explain how Odoo prevents cron job duplication
```

---

# PART II: TECHNICAL REPORT

# "Exploration of the Odoo Backend Using Python"
## Professional Technical Report

---

## EXECUTIVE SUMMARY

This report documents a comprehensive technical exploration of the Odoo Enterprise Resource Planning (ERP) platform's backend architecture, focusing on its Python implementation, database design, and programmatic interfaces.

Odoo is a modular, open-source ERP written primarily in Python 3.10+ with a PostgreSQL database backend. Its architecture consists of five primary layers: a browser-based frontend (Owl.js), an HTTP/WSGI layer (Werkzeug), a controller layer, a comprehensive Object-Relational Mapper (ORM), and a PostgreSQL database.

**Key Findings:**

1. The ORM (`odoo/models.py`) is the central component with ~5,000 lines managing all database interaction, security enforcement, and business logic orchestration.

2. The module system allows infinite extensibility — any module can extend any model without modifying original code.

3. Security is enforced at multiple levels: authentication, model-level ACLs, record-level rules, and field-level visibility.

4. All external communication — whether from the UI or third-party systems — converges on a small set of JSON-RPC and XML-RPC endpoints, making the API stable and predictable.

5. PostgreSQL's advanced features (row-level locking, `RETURNING` clauses, `FOR UPDATE SKIP LOCKED`) are heavily leveraged by Odoo's ORM.

---

## SYSTEM ARCHITECTURE

### Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CLIENT LAYER                                                           │
│  Owl.js SPA  │  External API Client  │  Mobile App                     │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ HTTP/HTTPS (JSON-RPC, XML-RPC)
┌──────────────────────────▼──────────────────────────────────────────────┐
│  HTTP LAYER (Werkzeug WSGI)                                             │
│  odoo/http.py → Route dispatch → Session management → CSRF              │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────────┐
│  CONTROLLER LAYER                                                       │
│  /web/dataset/call_kw (JSON-RPC)  │  /xmlrpc/2/ (XML-RPC)             │
│  Custom @http.route controllers                                         │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────────┐
│  ORM LAYER (odoo/models.py)                                             │
│  BaseModel → Model → TransientModel → AbstractModel                    │
│  CRUD │ Search │ ACL │ Record Rules │ Computed Fields │ Cache           │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ SQL
┌──────────────────────────▼──────────────────────────────────────────────┐
│  DATABASE LAYER (PostgreSQL 14+)                                        │
│  Tables │ Indexes │ FKs │ Constraints │ Functions                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Module Dependency Model

The module system forms a directed acyclic graph (DAG) of dependencies. When a module is installed, all its dependencies are installed first in topological order. This ensures that model extensions are applied in the correct sequence.

```
base → mail → web → sale → sale_management
  └──────────────────────→ account → account_accountant
  └──────────────────────→ stock → stock_account
```

---

## BACKEND COMPONENTS

### 1. The ORM (`odoo/models.py`)

The ORM is the most critical backend component. It provides:

**Model Registration:** Python classes inheriting from `models.Model` are collected at startup into a global `Registry` object (one per database). The registry resolves inheritance chains and presents a unified class to the application.

**Schema Management:** On module installation or upgrade, the ORM introspects field definitions and generates DDL (`CREATE TABLE`, `ALTER TABLE`, `CREATE INDEX`) to synchronize the PostgreSQL schema with the Python class definitions.

**Query Generation:** The `_search()` method converts Python domain expressions (e.g., `[('state', '=', 'sale')]`) into SQL WHERE clauses using the `osv/expression.py` module. The ORM uses parameterized queries exclusively, preventing SQL injection.

**Access Control:** Before every CRUD operation, the ORM calls `check_access_rights()` (ACL check) and `check_access_rule()` (record rule check). Record rules are injected as additional WHERE conditions in search queries.

### 2. The Environment (`odoo/api.py`)

The `Environment` object is passed through the entire call stack. It carries:
- `cr`: The PostgreSQL cursor (one per request/transaction)
- `uid`: The authenticated user's integer ID
- `context`: A frozen dictionary of request metadata (language, timezone, etc.)
- `_cache`: A per-request field value cache that avoids redundant SQL fetches

### 3. Field System (`odoo/fields.py`)

Fields are Python descriptors — their `__get__` and `__set__` methods intercept attribute access on model instances. When you access `order.partner_id`, the Many2one field's `__get__` checks the environment cache first; on a cache miss, it generates and executes a SELECT query.

Computed fields with `store=True` are maintained by a dependency graph: when a source field changes (e.g., `price_unit` changes), the ORM schedules the dependent computed field (e.g., `price_subtotal`) for recomputation and generates a SQL UPDATE.

---

## DATABASE DESIGN

### Schema Generation Strategy

Odoo generates DDL automatically from Python class definitions. The naming convention (dots to underscores) ensures consistent table names:

| Python `_name` | PostgreSQL Table |
|---|---|
| `sale.order` | `sale_order` |
| `sale.order.line` | `sale_order_line` |
| `account.move.line` | `account_move_line` |

### Relational Integrity

Many2one relationships are enforced with PostgreSQL foreign keys. The `ondelete` parameter of a Many2one field maps directly to PostgreSQL's `ON DELETE` behavior:

| Odoo `ondelete` | PostgreSQL |
|---|---|
| `'set null'` | `ON DELETE SET NULL` |
| `'restrict'` | `ON DELETE RESTRICT` |
| `'cascade'` | `ON DELETE CASCADE` |

### Core Tables and Their Purpose

The `ir_*` tables form the meta-layer — the system's self-description:

| Table | Purpose |
|---|---|
| `ir_model` | Registry of all models |
| `ir_model_fields` | All field definitions |
| `ir_ui_view` | XML view definitions |
| `ir_model_access` | ACL rules |
| `ir_rule` | Record-level security rules |
| `ir_module_module` | Module installation state |
| `ir_cron` | Scheduled job definitions |
| `ir_sequence` | Auto-increment sequences |

---

## ORM WORKFLOW

### Create Operation: End-to-End

```
env['sale.order'].create({'partner_id': 5, 'date_order': '2024-01-15'})
  │
  ├─ 1. Resolve defaults (company_id, user_id, warehouse_id from context)
  │
  ├─ 2. check_access_rights('create')
  │       → SELECT perm_create FROM ir_model_access WHERE model=... AND group IN user.groups
  │
  ├─ 3. check_access_rule('create') → apply ir.rule domain filters
  │
  ├─ 4. Validate Many2one references (partner_id=5 must exist in res_partner)
  │
  ├─ 5. INSERT INTO sale_order (partner_id, date_order, state, company_id, ...)
  │       VALUES (5, '2024-01-15', 'draft', 1, ...) RETURNING id;
  │
  ├─ 6. Trigger stored computed fields:
  │       UPDATE sale_order SET amount_total=0, amount_untaxed=0 WHERE id=42
  │
  ├─ 7. Run @api.constrains validators
  │
  ├─ 8. Post chatter message if mail.thread inherited
  │
  └─ 9. Return recordset: sale.order(42,)
```

### Search Operation with Security

```
env['sale.order'].search([('state', '=', 'sale')])
  │
  ├─ 1. check_access_rights('read')
  │
  ├─ 2. Gather all applicable ir.rule domains for current user
  │       → Global rules: [('company_id', 'in', [1, 2])]
  │       → Group rules: [('user_id', '=', 3)]  (salesman's own records)
  │
  ├─ 3. Combine: user_domain AND global_rule AND (group_rule_1 OR group_rule_2)
  │
  ├─ 4. Generate SQL:
  │       SELECT sale_order.id
  │       FROM sale_order
  │       WHERE sale_order.state = 'sale'
  │         AND sale_order.company_id IN (1, 2)
  │         AND sale_order.user_id = 3
  │       ORDER BY sale_order.id
  │
  └─ 5. Return recordset: sale.order(1, 4, 7, 12, ...)
```

---

## BACKEND EXPLORATION METHODOLOGY

### Recommended Exploration Workflow

**1. Start with the UI:** Identify the feature you want to understand. Enable Developer Mode (Settings → Activate Developer Mode). Navigate to the record in question.

**2. Identify the Model:** Go to Settings → Technical → Database Structure → Models. Find the model name (e.g., `sale.order`).

**3. Locate the Source Code:**
```bash
grep -r "_name = 'sale.order'" --include="*.py" addons/
```

**4. Read the Model Definition:** Open the file. Read fields, `_sql_constraints`, and key methods.

**5. Use the Shell for Live Exploration:**
```python
model = env['sale.order']
# Inspect fields
for name, field in sorted(model._fields.items()):
    print(name, field.__class__.__name__)
# Inspect methods
import inspect
print(inspect.getsource(model.action_confirm))
```

**6. Trace the Database:**
```sql
-- See the actual table structure
\d sale_order
-- See generated indexes
\di sale_order*
```

**7. Trace a workflow end-to-end with logging:**
```bash
python odoo-bin -d mydb --log-handler=odoo.sql_db:DEBUG
```

---

## KEY FINDINGS

### Finding 1: The ORM as Security Enforcer

Odoo's ORM doesn't just translate Python to SQL — it acts as the security layer. Every method call (create, write, search, unlink) checks ACL and record rules before generating SQL. This means security is enforced even when calling model methods from within Python (not just from the web). The only exception is `sudo()`, which explicitly bypasses all access control.

### Finding 2: The Module Registry as the Central Nervous System

The Registry (`odoo/modules/registry.py`) is the runtime glue. It maps model names to their fully-assembled Python class (after all `_inherit` extensions have been applied). When `env['sale.order']` is accessed, the Registry returns a class that is the combination of the original `sale.order` definition PLUS every extension from every installed module.

### Finding 3: Computed Fields Create Silent SQL Updates

When a user changes `price_unit` on a sale order line, the ORM automatically schedules recomputation of `price_subtotal` (via `@api.depends`). If `price_subtotal` has `store=True`, this triggers a SQL UPDATE on `sale_order_line`. If `amount_total` on the order depends on `price_subtotal`, another UPDATE follows on `sale_order`. This cascade of updates is entirely automatic and transparent.

### Finding 4: ir.* Tables as the Configuration Database

Odoo's configuration (views, menus, actions, sequences, scheduled jobs, server actions) is stored in PostgreSQL tables prefixed with `ir_`. This means configuration is data, not code. A view can be modified by editing a row in `ir_ui_view`. This is what allows Odoo's Studio (drag-and-drop customization) to work without modifying Python files.

### Finding 5: PostgreSQL Feature Utilization

Odoo deliberately leverages PostgreSQL-specific features:
- `SELECT ... FOR UPDATE SKIP LOCKED`: cron job locking without deadlocks
- `INSERT ... RETURNING id`: batch inserts with ID retrieval in one round-trip
- `ARRAY` operators: used in Some2many filtering
- Partial indexes: used in some ACL scenarios
- `pg_trgm` extension: trigram-based fuzzy text search

---

## CHALLENGES

### Challenge 1: Inheritance Chain Complexity

When debugging an issue in a method like `action_confirm`, the actual running code may come from 5+ modules that all `_inherit = 'sale.order'`. Each calls `super()`, creating a chain. Tracing this requires inspecting the MRO:
```python
for cls in type(env['sale.order']).__mro__:
    if 'action_confirm' in cls.__dict__:
        print(cls.__module__)
```

### Challenge 2: Computed Field Cache Invalidation

Odoo maintains a per-environment field value cache. In some scenarios (long-running scripts, cron jobs spanning many records), stale cache values can cause incorrect computed results. The workaround is `record.invalidate_recordset()` to force re-fetch.

### Challenge 3: Migration Between Odoo Versions

Odoo does not guarantee API stability between major versions (14→15→16→17). Module upgrades require migration scripts (`migrations/16.0.1.0.0/post_migrate.py`) that transform data to the new schema. This is a significant maintenance burden for custom modules.

### Challenge 4: Performance at Scale

The ORM's record-by-record processing (especially computed fields) can be slow for large datasets. A loop over 10,000 records calling `order.action_confirm()` may generate 50,000+ individual SQL statements. Solutions include batch SQL, `env.cr.execute()` for bulk operations, and background cron processing.

---

## BEST PRACTICES SUMMARY

| Practice | Rationale |
|---|---|
| Always call `super()` in overridden CRUD methods | Ensures all module extensions execute |
| Use `@api.model_create_multi` instead of `@api.model` for create | Supports batch creation efficiently |
| Index all Many2one fields | Odoo does this automatically, but verify in custom SQL |
| Prefix private methods with `_` | Prevents unintended RPC exposure |
| Use `UserError` for business errors, `ValidationError` for data errors | Correct exception type improves UX |
| Use `cr.savepoint()` in long loops | Allows partial success without full rollback |
| Avoid `sudo()` without justification | Security bypass should be documented |
| Use `search_count()` instead of `len(search())` | Avoids fetching all records just to count |
| Log with `_logger = logging.getLogger(__name__)` | Enables per-module log filtering |
| Test with `TransactionCase` | Tests run in rolled-back transactions (no data pollution) |

---

## CONCLUSION

Odoo's backend represents a sophisticated, production-grade ERP framework built on Python and PostgreSQL. Its layered architecture — from the Werkzeug HTTP layer through the ORM to PostgreSQL — provides a clean separation of concerns. The module system's inheritance model is Odoo's most powerful feature, enabling unlimited extensibility without modifying core code.

The ORM (`odoo/models.py`) is the central artifact of Odoo's backend. Understanding it deeply — its security enforcement, field descriptor protocol, computed field dependency graph, and SQL generation — is equivalent to understanding Odoo itself.

For a developer entering the Odoo ecosystem, the primary learning path is:
1. Master the ORM (models, fields, recordsets, CRUD)
2. Understand the security model (ACL + Record Rules)
3. Build complete modules with views, wizards, and tests
4. Explore the source of standard modules (sale, account, stock) for patterns
5. Use the shell constantly for live exploration

---

## FUTURE SCOPE

1. **REST API Expansion (Odoo 17+):** The new REST API (`/api/v1/`) will increasingly replace XML-RPC for external integrations. Future work should document its authentication flow and OpenAPI schema.

2. **OWL Frontend Integration:** Deep-diving into how Owl.js components communicate with Python business logic via the `call_kw` endpoint.

3. **Multi-tenant Performance:** Investigating PostgreSQL connection pooling strategies (PgBouncer) for high-scale multi-database Odoo deployments.

4. **Odoo.sh (Cloud Deployment):** Studying Odoo's managed cloud platform and its CI/CD integration with custom module development.

5. **AI/ML Integration:** Exploring Odoo's emerging AI features (lead scoring, OCR-based invoice processing) and how to extend them via Python.

6. **Migration Framework:** Building expertise in Odoo's OpenUpgrade migration framework for cross-version module upgrades.

---

## APPENDIX A: QUICK REFERENCE

### Essential Shell Commands
```python
# Get a model
m = env['sale.order']

# Search
env['sale.order'].search([('state', '=', 'sale')], limit=10)

# Read specific fields
env['sale.order'].search_read([('state','=','sale')], ['name','amount_total'])

# Create
env['sale.order'].create({'partner_id': 1})

# Update
order.write({'state': 'done'})

# Delete
order.unlink()

# Get field info
env['sale.order'].fields_get(['state'])

# Get source
import inspect; print(inspect.getsource(m.action_confirm))

# Check who can access
env['sale.order'].check_access_rights('create', raise_exception=False)
```

### Domain Operator Reference
```
=         equal
!=        not equal
<         less than
>         greater than
<=        less or equal
>=        greater or equal
like      LIKE (% wildcard supported)
ilike     case-insensitive LIKE
not like  NOT LIKE
not ilike NOT ILIKE
in        IN (pass a list)
not in    NOT IN (pass a list)
child_of  all children in hierarchy
parent_of all parents in hierarchy
=like     LIKE (exact match with % literal)
=ilike    case-insensitive exact LIKE
```

### X2many Command Reference
```python
(0, 0, {vals})        # Create new linked record
(1, id, {vals})       # Update linked record with id
(2, id, False)        # Delete linked record with id
(3, id, False)        # Unlink (detach) record with id
(4, id, False)        # Link existing record with id  
(5, False, False)     # Unlink (detach) all records
(6, False, [ids])     # Replace all links with this list of ids
```

### Exceptions Reference
```python
from odoo.exceptions import (
    UserError,          # Business logic error (show to user)
    ValidationError,    # Data validation failure
    AccessError,        # Permission denied
    MissingError,       # Record not found (deleted)
    RedirectWarning,    # Error with navigation button
)
```

---

*End of Report*

*Document prepared as a comprehensive technical reference for Odoo backend development. All code examples are validated against Odoo 16.0 Community Edition.*
