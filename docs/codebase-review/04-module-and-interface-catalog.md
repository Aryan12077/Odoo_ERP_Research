# 04 — Module and Interface Catalog

## 1. Top-Level Module Inventory

| Module / Path | Responsibility | Key Classes / Symbols | Inputs / Outputs | Dependencies | Consumed By | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`config.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS%20Research/config.py) | Environment configuration management. | `OdooConfig`, `TargetDBConfig`, `get_odoo_config()`, `get_target_db_config()` | Inputs: `.env`, OS env.<br/>Outputs: Typed config dataclasses. | `python-dotenv`, `dataclasses`, `os` | `connector.py`, `db_loader.py`, `setup_db.py` | Validates required keys and sets fallback ports/timeouts. |
| [`connector.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS%20Research/connector.py) | Odoo JSON-RPC / XML-RPC client. | `OdooClient`, `authenticate()`, `search_read()`, `search_count()`, `execute_kw()` | Inputs: RPC payloads, domain filters.<br/>Outputs: Deserialized lists of model dicts. | `requests`, `config.py` | `run_pipeline.py`, `pipelines/*`, `fetch_*` | Implements retryable JSON-RPC 2.0 transport over HTTPS. |
| [`db_loader.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS%20Research/db_loader.py) | Target PostgreSQL ingestion and procedure manager. | `DWHLoader`, `load_staging_and_merge()`, `truncate_table()`, `test_connection()` | Inputs: Target table name, list of row dicts.<br/>Outputs: Ingestion summary dict. | `psycopg2`, `config.py`, `uuid` | `run_pipeline.py`, `pipelines/base.py`, `setup_db.py` | Handles `execute_values` chunking and PL/pgSQL procedure calls. |
| [`run_pipeline.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS%20Research/run_pipeline.py) | Master CLI pipeline runner and orchestrator. | `main()`, `REGISTRY`, `DOMAINS` | Inputs: CLI args (`--domain`, `--extractor`, `--load`, `--truncate`, `--limit`).<br/>Outputs: Formatted console execution summary. | `argparse`, `connector.py`, `db_loader.py`, `pipelines/*` | CLI Operators, Scheduled cron jobs | Master entry point for all data ingestion tasks. |
| [`setup_db.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS%20Research/setup_db.py) | Target schema DDL & stored procedure provisioning. | `setup_schema()` | Inputs: `DAL_BKP_08042026` dump file.<br/>Outputs: Target DB schema, 43 tables, 21 stored procedures. | `re`, `db_loader.py`, `config.py` | Admin setup workflows | Idempotently provisions tables and procedures. |
| [`pipelines/base.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS%20Research/pipelines/base.py) | Abstract extractor base class and transformation utilities. | `BaseExtractor`, `get_m2o_id()`, `get_m2o_name()`, `pad_code()`, `safe_num()`, `parse_date()` | Inputs: Raw Odoo types.<br/>Outputs: Normalized types, execution status dict. | `datetime`, `re`, `typing` | All 18 domain extractors | Template method pattern for extraction and loading. |

---

## 2. Domain Extractor Catalog (18 Operational Extractors)

### A. Masters Domain (`pipelines/masters/`)

| Extractor Class | File Path | Target Table | Target Temp Table | Odoo Source Model | Primary Keys / Business Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CompanyMasterExtractor` | [`pipelines/masters/company.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/company.py) | `COMPANY_MASTER` | `COMPANY_MASTER_TEMP` | `res.company` | `COMPANY_CODE` |
| `BranchMasterExtractor` | [`pipelines/masters/branch.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/branch.py) | `BRANCH_MASTER` | `BRANCH_MASTER_TEMP` | `res.company` / `stock.warehouse` | `BRANCH_ID`, `COMPANY_CODE` |
| `CurrencyMasterExtractor` | [`pipelines/masters/currency.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/currency.py) | `CURRENCY_MASTER` | `CURRENCY_MASTER_TEMP` | `res.currency` | `CURRENCY_CODE` |
| `ChartOfAccountExtractor` | [`pipelines/masters/accounts.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/accounts.py) | `CHART_OF_ACCOUNT` | `CHART_OF_ACCOUNT_TEMP` | `account.account` | `"Account Code"`, `COMPANY_CODE` |
| `AccountTypeExtractor` | [`pipelines/masters/accounts.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/accounts.py) | `ACCOUNT_TYPE` | `ACCOUNT_TYPE_TEMP` | `account.account` | `ACCOUNT_CODE`, `COMPANY_CODE` |
| `CustomerMasterExtractor` | [`pipelines/masters/customer.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/customer.py) | `CUSTOMER_MASTER` | `CUSTOMER_MASTER_TEMP` | `res.partner` (`customer_rank > 0`) | `CUSTOMER_CODE`, `BRANCH_ID`, `COMPANY_CODE` |
| `SupplierMasterExtractor` | [`pipelines/masters/supplier.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/supplier.py) | `SUPPLIER_MASTER` | `SUPPLIER_MASTER_TEMP` | `res.partner` (`supplier_rank > 0`) | `SUPPLIER_CODE`, `BRANCH_ID`, `COMPANY_CODE` |
| `ProductMasterExtractor` | [`pipelines/masters/product.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/masters/product.py) | `PRODUCT_MASTER` | `PRODUCT_MASTER_TEMP` | `product.template` + `product.category` | `PRODUCT_CODE`, `BRANCH_ID`, `COMPANY_CODE` |

### B. Sales Domain (`pipelines/sales/`)

| Extractor Class | File Path | Target Table | Target Temp Table | Odoo Source Model | Primary Keys / Business Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SalesDataExtractor` | [`pipelines/sales/sales_data.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/sales/sales_data.py) | `SALES_DATA` | `SALES_DATA_TEMP` | `account.move.line` (`out_invoice`/`refund`) | `INVOICE_NUMBER`, `PRODUCT_CODE`, `CUSTOMER_CODE`, `INVOICE_DATE` |
| `MonthlySaleExtractor` | [`pipelines/sales/monthly_sale.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/sales/monthly_sale.py) | `MONTHLY_SALE` | `MONTHLY_SALE_TEMP` | `account.move` (aggregated) | `ACCOUNT_CODE`, `FOR_MONTH`, `BRANCH_ID`, `COMPANY_CODE` |

### C. Purchase Domain (`pipelines/purchase/`)

| Extractor Class | File Path | Target Table | Target Temp Table | Odoo Source Model | Primary Keys / Business Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `PurchaseDataExtractor` | [`pipelines/purchase/purchase_data.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/purchase/purchase_data.py) | `PURCHASE_DATA` | `PURCHASE_DATA_TEMP` | `purchase.order.line` + `purchase.order` + `stock.picking` | `PURCHASE_ORDER_NUMBER`, `ITEM_CODE`, `SUPPLIER_CODE`, `PURCHASE_DATE`, `GRN_NUMBER` |
| `MonthlyPurchaseExtractor` | [`pipelines/purchase/monthly_purchase.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/purchase/monthly_purchase.py) | `MONTHLY_PURCHASE` | `MONTHLY_PURCHASE_TEMP` | `account.move` (`in_invoice`/`refund` aggregated) | `ACCOUNT_CODE`, `FOR_MONTH`, `BRANCH_ID`, `COMPANY_CODE` |

### D. Inventory Domain (`pipelines/inventory/`)

| Extractor Class | File Path | Target Table | Target Temp Table | Odoo Source Model | Primary Keys / Business Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `InventoryAgeingExtractor` | [`pipelines/inventory/inventory_ageing.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/inventory/inventory_ageing.py) | `INVENTORY_AGEING` | `INVENTORY_AGEING_TEMP` | `stock.quant` + `product.product` | `PRODUCT_CODE`, `WAREHOUSE_ID`, `INVENTORY_DATE`, `BRANCH_ID` |

### E. Finance Domain (`pipelines/finance/`)

| Extractor Class | File Path | Target Table | Target Temp Table | Odoo Source Model | Primary Keys / Business Keys |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TransactionExtractor` | [`pipelines/finance/transaction.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/finance/transaction.py) | `TRANSACTION` | `TRANSACTION_TEMP` | `account.move.line` (posted GL lines) | `ACCOUNT_CODE`, `VOUCHER_NUMBER`, `VOUCHER_DATE`, `TRANSACTION_TYPE` |
| `AccountReceivableExtractor` | [`pipelines/finance/account_receivable.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/finance/account_receivable.py) | `ACCOUNT_RECEIVABLE` | `ACCOUNT_RECEIVABLE_TEMP` | `account.move.line` (`asset_receivable`, residual != 0) | `VOUCHER_NUMBER`, `VOUCHER_DATE`, `ACCOUNT_CODE`, `INVOICE_NUMBER`, `INVOICE_DATE` |
| `AccountPayableExtractor` | [`pipelines/finance/account_payable.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/finance/account_payable.py) | `ACCOUNT_PAYABLE` | `ACCOUNT_PAYABLE_TEMP` | `account.move.line` (`liability_payable`, residual != 0) | `VOUCHER_NUMBER`, `VOUCHER_DATE`, `ACCOUNT_CODE`, `INVOICE_NUMBER`, `INVOICE_DATE` |
| `MonthlyCollectionExtractor` | [`pipelines/finance/monthly_collection.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/finance/monthly_collection.py) | `MONTHLY_COLLECTION` | `MONTHLY_COLLECTION_TEMP` | `account.move.line` (credits on AR aggregated) | `BRANCH_CODE`, `ACCOUNT_CODE`, `FOR_MONTH`, `COMPANY_CODE` |
| `MonthlyPaymentExtractor` | [`pipelines/finance/monthly_payment.py`](file:///d:/ARYAN%20GUPTA%20OLD%20LAPTOP%20BACKUP/PROJECTS/ODOO%20ERP%20Research/pipelines/finance/monthly_payment.py) | `MONTHLY_PAYMENT` | `MONTHLY_PAYMENT_TEMP` | `account.move.line` (debits on AP aggregated) | `BRANCH_ID`, `ACCOUNT_CODE`, `FOR_MONTH`, `COMPANY_CODE` |

---

## 3. Public Interfaces & Contracts

### BaseExtractor Interface (`pipelines/base.py`)
```python
class BaseExtractor:
    target_table: str       # Name of destination table (e.g., 'SALES_DATA')
    procedure_name: str    # Optional stored procedure override (e.g., 'sp_update_sales_data')

    def extract(self, client: OdooClient) -> list[dict[str, Any]]:
        """Abstract method implemented by subclasses to extract and map Odoo records."""
        raise NotImplementedError

    def run(self, client: OdooClient, loader: Optional[DWHLoader] = None) -> dict[str, Any]:
        """Template method orchestrating extraction, timing, record counting, and database load."""
```

### DWHLoader Interface (`db_loader.py`)
```python
class DWHLoader:
    def __init__(self, config: Optional[TargetDBConfig] = None): ...
    def test_connection(self) -> dict[str, Any]: ...
    def truncate_table(self, table_name: str, include_temp: bool = True) -> None: ...
    def load_staging_and_merge(
        self,
        table_name: str,
        records: list[dict[str, Any]],
        procedure_name: Optional[str] = None
    ) -> dict[str, Any]: ...
```

### OdooClient Interface (`connector.py`)
```python
class OdooClient:
    def __init__(self, config: Optional[OdooConfig] = None): ...
    def authenticate(self) -> int: ...
    def search_read(
        self,
        model: str,
        domain: Optional[list] = None,
        fields: Optional[list[str]] = None,
        limit: int = 0,
        offset: int = 0,
        order: str = ""
    ) -> list[dict[str, Any]]: ...
    def search_count(self, model: str, domain: Optional[list] = None) -> int: ...
```

---

## 4. Document Links

- [Architecture and Components](02-architecture-and-components.md)
- [Runtime Flows and Data Flow](03-runtime-flows-and-data-flow.md)
- [Configuration, Integrations, and Data](05-configuration-integrations-and-data.md)
- [Developer KT Guide](09-developer-kt-guide.md)

