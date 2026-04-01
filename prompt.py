from database import get_data_summary

SCHEMA_DDL = """
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerCode VARCHAR(50) UNIQUE NOT NULL,
    CustomerName NVARCHAR(200) NOT NULL,
    Email NVARCHAR(200),
    Phone NVARCHAR(50),
    BillingCity NVARCHAR(100),
    BillingCountry NVARCHAR(100),
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Vendors (
    VendorId INT PRIMARY KEY,
    VendorCode VARCHAR(50) UNIQUE NOT NULL,
    VendorName NVARCHAR(200) NOT NULL,
    Email NVARCHAR(200),
    Phone NVARCHAR(50),
    City NVARCHAR(100),
    Country NVARCHAR(100),
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Sites (
    SiteId INT PRIMARY KEY,
    SiteCode VARCHAR(50) UNIQUE NOT NULL,
    SiteName NVARCHAR(200) NOT NULL,
    City NVARCHAR(100),
    Country NVARCHAR(100),
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Locations (
    LocationId INT PRIMARY KEY,
    SiteId INT NOT NULL REFERENCES Sites(SiteId),
    LocationCode VARCHAR(50) NOT NULL,
    LocationName NVARCHAR(200) NOT NULL,
    ParentLocationId INT REFERENCES Locations(LocationId),
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Items (
    ItemId INT PRIMARY KEY,
    ItemCode NVARCHAR(100) UNIQUE NOT NULL,
    ItemName NVARCHAR(200) NOT NULL,
    Category NVARCHAR(100),
    UnitOfMeasure NVARCHAR(50),
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Assets (
    AssetId INT PRIMARY KEY,
    AssetTag VARCHAR(100) UNIQUE NOT NULL,
    AssetName NVARCHAR(200) NOT NULL,
    SiteId INT NOT NULL REFERENCES Sites(SiteId),
    LocationId INT REFERENCES Locations(LocationId),
    SerialNumber NVARCHAR(200),
    Category NVARCHAR(100),
    Status VARCHAR(30) NOT NULL DEFAULT 'Active',  -- Active, InRepair, Disposed
    Cost DECIMAL(18,2),
    PurchaseDate DATE,
    VendorId INT REFERENCES Vendors(VendorId)
);

CREATE TABLE Bills (
    BillId INT PRIMARY KEY,
    VendorId INT NOT NULL REFERENCES Vendors(VendorId),
    BillNumber VARCHAR(100) NOT NULL,
    BillDate DATE NOT NULL,
    DueDate DATE,
    TotalAmount DECIMAL(18,2) NOT NULL,
    Currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    Status VARCHAR(30) NOT NULL DEFAULT 'Open'  -- Open, Paid, Void
);

CREATE TABLE PurchaseOrders (
    POId INT PRIMARY KEY,
    PONumber VARCHAR(100) UNIQUE NOT NULL,
    VendorId INT NOT NULL REFERENCES Vendors(VendorId),
    PODate DATE NOT NULL,
    Status VARCHAR(30) NOT NULL DEFAULT 'Open',  -- Open, Approved, Closed, Cancelled
    SiteId INT REFERENCES Sites(SiteId)
);

CREATE TABLE PurchaseOrderLines (
    POLineId INT PRIMARY KEY,
    POId INT NOT NULL REFERENCES PurchaseOrders(POId),
    LineNumber INT NOT NULL,
    ItemCode NVARCHAR(100) NOT NULL,
    Description NVARCHAR(200),
    Quantity DECIMAL(18,4) NOT NULL,
    UnitPrice DECIMAL(18,4) NOT NULL
);

CREATE TABLE SalesOrders (
    SOId INT PRIMARY KEY,
    SONumber VARCHAR(100) UNIQUE NOT NULL,
    CustomerId INT NOT NULL REFERENCES Customers(CustomerID),
    SODate DATE NOT NULL,
    Status VARCHAR(30) NOT NULL DEFAULT 'Open',  -- Open, Shipped, Closed, Cancelled
    SiteId INT REFERENCES Sites(SiteId)
);

CREATE TABLE SalesOrderLines (
    SOLineId INT PRIMARY KEY,
    SOId INT NOT NULL REFERENCES SalesOrders(SOId),
    LineNumber INT NOT NULL,
    ItemCode NVARCHAR(100) NOT NULL,
    Description NVARCHAR(200),
    Quantity DECIMAL(18,4) NOT NULL,
    UnitPrice DECIMAL(18,4) NOT NULL
);

CREATE TABLE AssetTransactions (
    AssetTxnId INT PRIMARY KEY,
    AssetId INT NOT NULL REFERENCES Assets(AssetId),
    FromLocationId INT REFERENCES Locations(LocationId),
    ToLocationId INT REFERENCES Locations(LocationId),
    TxnType VARCHAR(30) NOT NULL,  -- Move, Adjust, Dispose, Create
    Quantity INT NOT NULL DEFAULT 1,
    TxnDate DATETIME2 NOT NULL,
    Note NVARCHAR(500)
);
"""


def build_system_prompt() -> str:
    data_summary = get_data_summary()

    return f"""You are an intelligent inventory management assistant for asap SYSTEMS.
You have full knowledge of the company's inventory database schema and current data.

## VALID TABLE NAMES (use ONLY these in SQL)
Customers, Vendors, Sites, Locations, Items, Assets, Bills,
PurchaseOrders, PurchaseOrderLines, SalesOrders, SalesOrderLines, AssetTransactions

## DATABASE SCHEMA (SQL Server DDL)
{SCHEMA_DDL}

## CURRENT DATABASE DATA (Knowledge Base — read to form your answer, do NOT use section headers as table names)
The headings below like "Assets Summary" or "Open POs" are labels for readability only.
They are NOT database table names. Never use them in SQL.
{data_summary}

## YOUR JOB
When the user asks an inventory or business question:
1. Read the Knowledge Base data above to derive the real answer with actual numbers.
2. Generate the correct SQL Server query using ONLY the real table names listed above.
3. Suggest 5 relevant follow-up questions.

## CRITICAL OUTPUT FORMAT
You MUST respond ONLY with valid JSON in exactly this structure — no markdown, no extra text:
{{
  "answer": "Your precise natural language answer using real numbers from the knowledge base above",
  "query": "SELECT ... valid SQL Server query using only real table names ...",
  "suggested_questions": [
    "Follow-up question 1?",
    "Follow-up question 2?",
    "Follow-up question 3?",
    "Follow-up question 4?",
    "Follow-up question 5?"
  ]
}}

## SQL RULES — STRICTLY FOLLOW
- ONLY use these table names: Customers, Vendors, Sites, Locations, Items, Assets,
  Bills, PurchaseOrders, PurchaseOrderLines, SalesOrders, SalesOrderLines, AssetTransactions
- NEVER invent table names. Never use names like AssetsSummary, ActiveAssets, OpenPOs, etc.
- Use SQL Server syntax (e.g., TOP instead of LIMIT)
- Always filter out Disposed assets with WHERE Status <> 'Disposed' unless user asks about disposed assets
- Use proper JOINs when referencing multiple tables
- The query must exactly match the intent of the answer

## ANSWER RULES
- Always use specific real numbers from the Knowledge Base data (e.g., "You have 19 active assets")
- Be concise but informative
- If the question is not about inventory/business data, politely redirect the user
"""
