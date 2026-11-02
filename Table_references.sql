-- ============================================================================
-- EVA_BI DATA WAREHOUSE - CONSOLIDATED TABLE DEFINITIONS (DDL REFERENCES)
-- Source: DAL_BKP_08042026 (PostgreSQL schema: EVA_BI)
-- Staging (_TEMP) tables omitted as they mirror target tables with 'Call ID'
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS "EVA_BI";

-- ============================================================================
-- MASTER TABLES
-- ============================================================================

-- Table: EVA_BI.COMPANY_MASTER
CREATE TABLE "EVA_BI"."COMPANY_MASTER" (
    "GROUP_COMPANY_CODE" character varying,
    "GROUP_COMPANY_NAME" character varying,
    "COMPANY_CODE" character varying,
    "COMPANY_NAME" character varying,
    "BASE_CURRENCY_CODE" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.BRANCH_MASTER
CREATE TABLE "EVA_BI"."BRANCH_MASTER" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "BRANCH" character varying,
    "LOCATION_TYPE" character varying,
    "LOCATION_CATEGORY" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.CUSTOMER_MASTER
CREATE TABLE "EVA_BI"."CUSTOMER_MASTER" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "CUSTOMER_CODE" integer,
    "CUSTOMER_NAME" character varying,
    "EXECUTIVE_ID" character varying,
    "EXECUTIVE" character varying,
    "CATEGORY_CODE" character varying,
    "CATEGORY" character varying,
    "ZONE_CODE" character varying,
    "AREA" character varying,
    "STATE_CODE" character varying,
    "STATE" character varying,
    "CITY_CODE" character varying,
    "CITY" character varying,
    "COUNTRY_CODE" character varying,
    "COUNTRY" character varying,
    "INDUSTRY_ID" character varying,
    "INDUSTRY" character varying,
    "TYPE_ID" character varying,
    "CUST_TYPE" character varying,
    "ACCOUNT_CODE" integer,
    "RID" numeric,
    "CREDIT_DAYS" numeric,
    "CREDIT_LIMIT" numeric,
    "BILL_AREA" character varying,
    "BILL_REGION" character varying,
    "AVERAGE_BILLING" numeric,
    "AVERAGE_PAYMENT" numeric,
    "CURRENCY_CODE" integer,
    "MASTER_ACCOUNT" numeric,
    "MASTER_ACCOUNT_NAME" character varying,
    "TELEPHONE" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.SUPPLIER_MASTER
CREATE TABLE "EVA_BI"."SUPPLIER_MASTER" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "SUPPLIER_CODE" integer,
    "SUPPLIER" character varying,
    "CATEGORY_CODE" character varying,
    "CATEGORY" character varying,
    "STATE_CODE" character varying,
    "STATE" character varying,
    "CITY_CODE" character varying,
    "CITY" character varying,
    "COUNTRY_CODE" character varying,
    "COUNTRY" character varying,
    "ACCOUNT_CODE" integer,
    "RID" numeric,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.PRODUCT_MASTER
CREATE TABLE "EVA_BI"."PRODUCT_MASTER" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "PRODUCT_CODE" character varying,
    "AEDESC" character varying,
    "MAKE" character varying,
    "OEM" character varying,
    "APP" character varying,
    "PARTNO2" character varying,
    "SIZE" character varying,
    "PRODUCT" character varying,
    "UNIT_CODE" character varying,
    "UNIT" character varying,
    "WEIGHT_UNIT" character varying,
    "KGS_FOR_PCS" numeric,
    "WEIGHT_PCS" numeric,
    "GROUP_CODE" character varying,
    "GROUP_NAME" character varying,
    "CLASSIFICATION_CODE" character varying,
    "CLASSIFICATION" character varying,
    "SUB_GROUP_CODE" character varying,
    "SUB_GROUP" character varying,
    "SUB_SUB_GROUP_CODE" character varying,
    "SUB_SUB_GROUP" character varying,
    "CREATION_DATE" timestamp without time zone,
    "BRAND_CODE" character varying,
    "BRAND" character varying,
    "FIRST_SALE_DATE" timestamp without time zone,
    "LAST_SALE_DATE" timestamp without time zone,
    "FIRST_PURCHASE_QUANTITY" numeric,
    "LAST_PURCHASE_QUANTITY" numeric,
    "FIRST_SALE_QUANTITY" numeric,
    "LAST_SALE_QUANTITY" numeric,
    "RID" numeric,
    "PRODUCT_PRICE" numeric,
    "PRODUCT_PRICE_USD" numeric,
    "SALE_PRICE" numeric,
    "SALE_PRICE_USD" numeric,
    "SBU_CODE" character varying,
    "SBU" character varying,
    "STOCK_QUANTITY" numeric,
    "REORDER_LEVEL" numeric,
    "LEAD_TIME_IN_DAYS" numeric,
    "WARRANTY_IN_MONTHS" numeric,
    "SUPPLIER" character varying,
    "DISCOUNT_PERCENTAGE" numeric,
    "TAX_RATE" numeric,
    "SHIPPING_COST" numeric,
    "STORAGE_LOCATION" character varying,
    "MIN_LEVEL" numeric,
    "MAX_LEVEL" numeric,
    "PO_PROCESS_DAYS" numeric,
    "LOGISTICS_DAYS" numeric,
    "SAFETY_STOCK" numeric,
    "FIRST_PURCHASE_DATE" timestamp without time zone,
    "LAST_PURCHASE_DATE" timestamp without time zone,
    "ABC" character varying,
    "VED" character varying,
    "PRINCIPAL_CODE" character varying,
    "PRINCIPAL" character varying,
    "STYLE" character varying,
    "CARTON_QUANTITY" numeric,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.CURRENCY_MASTER
CREATE TABLE "EVA_BI"."CURRENCY_MASTER" (
    "CURRENCY_CODE" integer,
    "CURRENCY" character varying,
    "DIVIDEND" numeric,
    "CONVERSION_FACTOR" numeric,
    "DIVIDEND_ABBREVIATION" character varying,
    "CURRENCY_UNICHAR" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.GEO_MASTER
CREATE TABLE "EVA_BI"."GEO_MASTER" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "BRANCH_NAME" character varying,
    "BRANCH_CITY" character varying,
    "BRANCH_COUNTRY" character varying,
    "BRANCH_TYPE" character varying,
    "BRANCH_SIZE" character varying,
    "BRANCH_AREA_IN_SQM" numeric,
    "STORE_ID" character varying,
    "STORE_NAME" character varying,
    "STORE_LOCATION" character varying,
    "STORE_TYPE" character varying,
    "STORE_AREA_IN_SQM" numeric,
    "STORE_CAPACITY_IN_K_LT" numeric,
    "WAREHOUSE_NAME" character varying,
    "WAREHOUSE_ID" character varying,
    "WAREHOUSE_TYPE" character varying,
    "WAREHOUSE_LOCATION" character varying,
    "WAREHOUSE_CAPACITY_IN_K_LT" numeric,
    "WAREHOUSE_GROUP" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.CHART_OF_ACCOUNT
CREATE TABLE "EVA_BI"."CHART_OF_ACCOUNT" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "GROUP_CODE" character varying,
    "GROUP" character varying,
    "S_GROUP_CODE" character varying,
    "S_GROUP" character varying,
    "SS_GROUP_CODE" character varying,
    "SS_GROUP" character varying,
    "SSS_GROUP_CODE" character varying,
    "SSS_GROUP" character varying,
    "SSSS_GROUP_CODE" character varying,
    "SSSS_GROUP" character varying,
    "SSSSS Group Code" character varying,
    "SSSSS_GROUP" character varying,
    "SSSSSS_GROUP_CODE" character varying,
    "SSSSSS_GROUP" character varying,
    "Account Code" integer,
    "Account Name" character varying,
    "Ledger Code" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.ACCOUNT_TYPE
CREATE TABLE "EVA_BI"."ACCOUNT_TYPE" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "ACCOUNT_CODE" integer,
    "ACCOUNT_TYPE" character varying,
    "ACCOUNT_FLAG" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.ANALYSIS_CRITERIA
CREATE TABLE "EVA_BI"."ANALYSIS_CRITERIA" (
    "Analysis Code" numeric,
    "Analysis Criteria" character varying,
    "Analysis Type" character varying,
    "Active" numeric,
    "Target Available" numeric,
    "Currency Code" integer,
    "Currency" character varying,
    "Currency Unichar" character varying,
    "Code" numeric,
    "Unit" character varying,
    "Dividend" numeric,
    "Short Form" character varying,
    "Long Form" character varying,
    "Long Text" character varying,
    "UOM" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.FISCAL_CALENDAR
CREATE TABLE "EVA_BI"."FISCAL_CALENDAR" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "Cy Start Date" timestamp without time zone,
    "Cy End Date" timestamp without time zone,
    "FY Start Date" timestamp without time zone,
    "FY End Date" timestamp without time zone,
    "Cy Year" character varying,
    "Fy Year" character varying,
    "Cy Rank" numeric,
    "Fy Rank" numeric,
    "Cy Qtr" character varying,
    "Fy Qtr" character varying,
    "Month Start Date" timestamp without time zone,
    "Month End Date" timestamp without time zone,
    "Month" character varying,
    "Cy Month No" bigint,
    "Fy Month No" bigint,
    "Week Start Date" timestamp without time zone,
    "Week End Date" timestamp without time zone,
    "Cy Week No" character varying,
    "Fy Week No" character varying,
    "Month Week No" character varying,
    "Date" timestamp without time zone,
    "Day" character varying,
    "Day Name" character varying,
    "Week Day" numeric,
    "Last Transaction Date" timestamp without time zone,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- ============================================================================
-- TRANSACTIONAL & SUBLEDGER TABLES
-- ============================================================================

-- Table: EVA_BI.SALES_DATA
CREATE TABLE "EVA_BI"."SALES_DATA" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "STORE_ID" character varying,
    "WAREHOUSE_ID" character varying,
    "CUSTOMER_CODE" integer,
    "INVOICE_DATE" timestamp without time zone,
    "INVOICE_NUMBER" character varying,
    "PRODUCT_CODE" character varying,
    "EXECUTIVE_ID" character varying,
    "EXECUTIVE" character varying,
    "INVOICE_CURRENCY" numeric,
    "EXCHANGE_RATE" numeric,
    "SALE_QUANTITY" numeric,
    "SALE_VALUE_USD" numeric,
    "SALE_VALUE_AUD" numeric,
    "COGS_USD" numeric,
    "COGS_AUD" numeric,
    "SALE_TYPE" character varying,
    "SALE_WO_TAX_USD" numeric,
    "SALE_WO_TAX_AUD" numeric,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.PURCHASE_DATA
CREATE TABLE "EVA_BI"."PURCHASE_DATA" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "SUPPLIER_CODE" integer,
    "PURCHASE_ORDER_NUMBER" character varying,
    "PURCHASE_DATE" timestamp without time zone,
    "PO_DELIVERY_DATE" character varying,
    "ITEM_CODE" character varying,
    "ORDERED_QUANTITY" numeric,
    "UNIT_PRICE" numeric,
    "GRN_NUMBER" character varying,
    "GRN_DATE" timestamp without time zone,
    "BILL_NUMBER" character varying,
    "CHALLAN_NUMBER" character varying,
    "CHALLAN_DATE" character varying,
    "GATE_ENTRY_NUMBER" character varying,
    "CHALLAN_QUANTITY" numeric,
    "RECEIVED_QUANTITY" numeric,
    "ACCEPTED_QUANTITY" numeric,
    "PURCHASE_VALUE" numeric,
    "PURCHASE_VALUE_BASE" numeric,
    "REJECTED_QUANTITY" numeric,
    "ACCOUNT_CODE" integer,
    "REJECTION_REASON" character varying,
    "GATE_ORDER_NUMBER" character varying,
    "ORDER_STATUS" character varying,
    "EXPECTED_DELIVERY_DATE" timestamp without time zone,
    "LEAD_TIME" numeric,
    "WAREHOUSE_ID" character varying,
    "ROW_ID" character varying,
    "BRANCH_ID" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.TRANSACTION
CREATE TABLE "EVA_BI"."TRANSACTION" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "ACCOUNT_CODE" integer,
    "VOUCHER_NUMBER" character varying,
    "VOUCHER_DATE" timestamp without time zone,
    "AMOUNT" numeric,
    "AMOUNT_BASE" numeric,
    "SERIAL_NUMBER" numeric,
    "TRANSACTION_TYPE" character varying,
    "TRANSACTION_TYPE_BASE" character varying,
    "AUTHORIZATION_FLAG" character varying,
    "VOUCHER_TYPE" character varying,
    "DUE_DATE" timestamp without time zone,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.ACCOUNT_RECEIVABLE
CREATE TABLE "EVA_BI"."ACCOUNT_RECEIVABLE" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "VOUCHER_NUMBER" character varying,
    "VOUCHER_DATE" timestamp without time zone,
    "ACCOUNT_CODE" integer,
    "INVOICE_NUMBER" character varying,
    "INVOICE_DATE" timestamp without time zone,
    "DUE_DATE" timestamp without time zone,
    "OUTSTANDING_DATE" timestamp without time zone,
    "INVOICE_AMOUNT" numeric,
    "OUTSTANDING" numeric,
    "CURRENCY_CODE" numeric,
    "AMOUNT_PAID" numeric,
    "OUTSTANDING_DAYS" numeric,
    "REGION" character varying,
    "INVOICE_AMOUNT_BASE" numeric,
    "INVOICE_AMOUNT_REPORTING" numeric,
    "OUTSTANDING_BASE" numeric,
    "OUTSTANDING_REPORTING" numeric,
    "AMOUNT_PAID_BASE" numeric,
    "AMOUNT_PAID_REPORTING" numeric,
    "CUSTOMER_CATEGORY" character varying,
    "DURATION1" numeric,
    "DURATION2" numeric,
    "DURATION3" numeric,
    "DURATION4" numeric,
    "DURATION5" numeric,
    "DURATION1_BASE" numeric,
    "DURATION2_BASE" numeric,
    "DURATION3_BASE" numeric,
    "DURATION4_BASE" numeric,
    "DURATION5_BASE" numeric,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.ACCOUNT_PAYABLE
CREATE TABLE "EVA_BI"."ACCOUNT_PAYABLE" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "VOUCHER_NUMBER" character varying,
    "VOUCHER_DATE" timestamp without time zone,
    "ACCOUNT_CODE" integer,
    "INVOICE_NUMBER" character varying,
    "INVOICE_DATE" timestamp without time zone,
    "DUE_DATE" timestamp without time zone,
    "OUTSTANDING_DATE" timestamp without time zone,
    "INVOICE_AMOUNT" numeric,
    "OUTSTANDING" numeric,
    "CURRENCY_CODE" numeric,
    "AMOUNT_PAID" numeric,
    "OUTSTANDING_DAYS" numeric,
    "REGION" character varying,
    "INVOICE_AMOUNT_BASE" numeric,
    "INVOICE_AMOUNT_REPORTING" numeric,
    "OUTSTANDING_BASE" numeric,
    "OUTSTANDING_REPORTING" numeric,
    "AMOUNT_PAID_BASE" numeric,
    "AMOUNT_PAID_REPORTING" numeric,
    "CUSTOMER_CATEGORY" character varying,
    "DURATION1" numeric,
    "DURATION2" numeric,
    "DURATION3" numeric,
    "DURATION4" numeric,
    "DURATION5" numeric,
    "DURATION1_BASE" numeric,
    "DURATION2_BASE" numeric,
    "DURATION3_BASE" numeric,
    "DURATION4_BASE" numeric,
    "DURATION5_BASE" numeric,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.INVENTORY_AGEING
CREATE TABLE "EVA_BI"."INVENTORY_AGEING" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "WAREHOUSE_ID" character varying,
    "PRODUCT_CODE" character varying,
    "BIN_NO" numeric,
    "CONSIGN_NO" numeric,
    "PURCHASE_DATE" timestamp without time zone,
    "INVENTORY_DATE" timestamp without time zone,
    "PURCHASE_QUANTITY" numeric,
    "TOTAL_CONSUMPTION" numeric,
    "REMAINING_QUANTITY" numeric,
    "REMAINING_VALUE_USD" numeric,
    "REMAINING_VALUE_AUD" numeric,
    "PURCHASE_VALUE_USD" numeric,
    "PURCHASE_VALUE_AUD" numeric,
    "ITEM_UNIT_COST_USD" numeric,
    "ITEM_UNIT_COST_AUD" numeric,
    "RETURN_QUANTITY" numeric,
    "SALE_QUANTITY" numeric,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- ============================================================================
-- MONTHLY AGGREGATIONS & SUMMARY TABLES
-- ============================================================================

-- Table: EVA_BI.MONTHLY_SALE
CREATE TABLE "EVA_BI"."MONTHLY_SALE" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "ACCOUNT_CODE" integer,
    "FOR_MONTH" timestamp without time zone,
    "SALE_VALUE_USD" numeric,
    "INVOICE_DATE" timestamp without time zone,
    "SALE_VALUE_AUD" numeric,
    "INVOICE_VALUE" numeric,
    "REGION" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.MONTHLY_PURCHASE
CREATE TABLE "EVA_BI"."MONTHLY_PURCHASE" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "ACCOUNT_CODE" integer,
    "FOR_MONTH" timestamp without time zone,
    "PURCHASE_VALUE" numeric,
    "PURCHASE_DATE" timestamp without time zone,
    "PURCHASE_VALUE_BASE" numeric,
    "INVOICE_VALUE" numeric,
    "REGION" character varying,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.MONTHLY_COLLECTION
CREATE TABLE "EVA_BI"."MONTHLY_COLLECTION" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_CODE" character varying,
    "ACCOUNT_CODE" integer,
    "FOR_MONTH" timestamp without time zone,
    "COLLECTION" numeric,
    "COLLECTION_BASE" numeric,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- Table: EVA_BI.MONTHLY_PAYMENT
CREATE TABLE "EVA_BI"."MONTHLY_PAYMENT" (
    "GROUP_COMPANY_CODE" character varying,
    "COMPANY_CODE" character varying,
    "BRANCH_ID" character varying,
    "ACCOUNT_CODE" integer,
    "FOR_MONTH" timestamp without time zone,
    "PAYMENT" numeric,
    "PAYMENT_BASE" numeric,
    "SNAPSHOT_DT" timestamp without time zone DEFAULT (now())::timestamp without time zone
);


-- ============================================================================
-- SYSTEM & AUDIT LOGS
-- ============================================================================

-- Table: EVA_BI.Data_Push_Agent_Log
CREATE TABLE "EVA_BI"."Data_Push_Agent_Log" (
    "Log_id" integer NOT NULL,
    "Log_Procedure" character varying(500),
    "Log_Status" character varying(2000),
    "Log_Time" timestamp without time zone DEFAULT now()
);

