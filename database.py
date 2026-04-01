import sqlite3
import threading

_local = threading.local()

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS Customers (
    CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerCode TEXT UNIQUE NOT NULL,
    CustomerName TEXT NOT NULL,
    Email TEXT,
    Phone TEXT,
    BillingCity TEXT,
    BillingCountry TEXT,
    IsActive INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Vendors (
    VendorId INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorCode TEXT UNIQUE NOT NULL,
    VendorName TEXT NOT NULL,
    Email TEXT,
    Phone TEXT,
    City TEXT,
    Country TEXT,
    IsActive INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Sites (
    SiteId INTEGER PRIMARY KEY AUTOINCREMENT,
    SiteCode TEXT UNIQUE NOT NULL,
    SiteName TEXT NOT NULL,
    City TEXT,
    Country TEXT,
    IsActive INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Locations (
    LocationId INTEGER PRIMARY KEY AUTOINCREMENT,
    SiteId INTEGER NOT NULL,
    LocationCode TEXT NOT NULL,
    LocationName TEXT NOT NULL,
    ParentLocationId INTEGER,
    IsActive INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
    FOREIGN KEY (ParentLocationId) REFERENCES Locations(LocationId)
);

CREATE TABLE IF NOT EXISTS Items (
    ItemId INTEGER PRIMARY KEY AUTOINCREMENT,
    ItemCode TEXT UNIQUE NOT NULL,
    ItemName TEXT NOT NULL,
    Category TEXT,
    UnitOfMeasure TEXT,
    IsActive INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Assets (
    AssetId INTEGER PRIMARY KEY AUTOINCREMENT,
    AssetTag TEXT UNIQUE NOT NULL,
    AssetName TEXT NOT NULL,
    SiteId INTEGER NOT NULL,
    LocationId INTEGER,
    SerialNumber TEXT,
    Category TEXT,
    Status TEXT NOT NULL DEFAULT 'Active',
    Cost REAL,
    PurchaseDate TEXT,
    VendorId INTEGER,
    FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
    FOREIGN KEY (LocationId) REFERENCES Locations(LocationId),
    FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
);

CREATE TABLE IF NOT EXISTS Bills (
    BillId INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorId INTEGER NOT NULL,
    BillNumber TEXT NOT NULL,
    BillDate TEXT NOT NULL,
    DueDate TEXT,
    TotalAmount REAL NOT NULL,
    Currency TEXT NOT NULL DEFAULT 'USD',
    Status TEXT NOT NULL DEFAULT 'Open',
    FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
);

CREATE TABLE IF NOT EXISTS PurchaseOrders (
    POId INTEGER PRIMARY KEY AUTOINCREMENT,
    PONumber TEXT UNIQUE NOT NULL,
    VendorId INTEGER NOT NULL,
    PODate TEXT NOT NULL,
    Status TEXT NOT NULL DEFAULT 'Open',
    SiteId INTEGER,
    FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId),
    FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
);

CREATE TABLE IF NOT EXISTS PurchaseOrderLines (
    POLineId INTEGER PRIMARY KEY AUTOINCREMENT,
    POId INTEGER NOT NULL,
    LineNumber INTEGER NOT NULL,
    ItemCode TEXT NOT NULL,
    Description TEXT,
    Quantity REAL NOT NULL,
    UnitPrice REAL NOT NULL,
    FOREIGN KEY (POId) REFERENCES PurchaseOrders(POId)
);

CREATE TABLE IF NOT EXISTS SalesOrders (
    SOId INTEGER PRIMARY KEY AUTOINCREMENT,
    SONumber TEXT UNIQUE NOT NULL,
    CustomerId INTEGER NOT NULL,
    SODate TEXT NOT NULL,
    Status TEXT NOT NULL DEFAULT 'Open',
    SiteId INTEGER,
    FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerID),
    FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
);

CREATE TABLE IF NOT EXISTS SalesOrderLines (
    SOLineId INTEGER PRIMARY KEY AUTOINCREMENT,
    SOId INTEGER NOT NULL,
    LineNumber INTEGER NOT NULL,
    ItemCode TEXT NOT NULL,
    Description TEXT,
    Quantity REAL NOT NULL,
    UnitPrice REAL NOT NULL,
    FOREIGN KEY (SOId) REFERENCES SalesOrders(SOId)
);

CREATE TABLE IF NOT EXISTS AssetTransactions (
    AssetTxnId INTEGER PRIMARY KEY AUTOINCREMENT,
    AssetId INTEGER NOT NULL,
    FromLocationId INTEGER,
    ToLocationId INTEGER,
    TxnType TEXT NOT NULL,
    Quantity INTEGER NOT NULL DEFAULT 1,
    TxnDate TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Note TEXT,
    FOREIGN KEY (AssetId) REFERENCES Assets(AssetId)
);
"""

SEED_SQL = """
-- Sites
INSERT OR IGNORE INTO Sites (SiteCode, SiteName, City, Country) VALUES
('CAIRO-HQ', 'Cairo Headquarters', 'Cairo', 'Egypt'),
('ALEX-01',  'Alexandria Branch',  'Alexandria', 'Egypt'),
('RUH-01',   'Riyadh Office',      'Riyadh', 'Saudi Arabia'),
('DXB-01',   'Dubai Office',       'Dubai', 'UAE'),
('NY-01',    'New York Office',    'New York', 'USA');

-- Vendors
INSERT OR IGNORE INTO Vendors (VendorCode, VendorName, Email, City, Country) VALUES
('DELL-EG',   'Dell Technologies Egypt',   'sales@dell.eg',      'Cairo',    'Egypt'),
('HP-ME',     'HP Middle East',            'sales@hp-me.com',    'Dubai',    'UAE'),
('LENOVO-SA', 'Lenovo Saudi Arabia',       'info@lenovo.sa',     'Riyadh',   'Saudi Arabia'),
('CISCO-EG',  'Cisco Egypt',               'sales@cisco.eg',     'Cairo',    'Egypt'),
('FURNI-CO',  'Office Furniture Co.',      'info@furnco.com',    'Cairo',    'Egypt');

-- Locations
INSERT OR IGNORE INTO Locations (SiteId, LocationCode, LocationName) VALUES
(1, 'FLOOR-1', 'Cairo HQ - Floor 1'),
(1, 'FLOOR-2', 'Cairo HQ - Floor 2'),
(1, 'DATACENTER', 'Cairo HQ - Data Center'),
(2, 'MAIN',   'Alexandria - Main Hall'),
(3, 'OFFICE-A', 'Riyadh - Office A'),
(4, 'OFFICE-B', 'Dubai - Office B'),
(5, 'SUITE-1', 'New York - Suite 101');

-- Customers
INSERT OR IGNORE INTO Customers (CustomerCode, CustomerName, Email, Phone, BillingCity, BillingCountry) VALUES
('CUST-001', 'Nile Tech Solutions',     'billing@niletech.com',    '+20-2-12345678', 'Cairo',     'Egypt'),
('CUST-002', 'Gulf Systems LLC',        'finance@gulfsys.ae',      '+971-4-9876543', 'Dubai',     'UAE'),
('CUST-003', 'Al-Riyadh Enterprises',  'ap@alriyadh.sa',          '+966-1-5554321', 'Riyadh',    'Saudi Arabia'),
('CUST-004', 'Eastern Trading Co.',    'accounts@eastrade.com',   '+20-3-7654321',  'Alexandria','Egypt'),
('CUST-005', 'Global Connect Inc.',    'info@globalconnect.com',  '+1-212-5550100', 'New York',  'USA');

-- Items
INSERT OR IGNORE INTO Items (ItemCode, ItemName, Category, UnitOfMeasure) VALUES
('LAPTOP-DELL-15',  'Dell Latitude 15 Laptop',       'Laptop',   'Unit'),
('LAPTOP-LNV-14',   'Lenovo ThinkPad 14 Laptop',     'Laptop',   'Unit'),
('MONITOR-HP-24',   'HP 24-inch Monitor',            'Monitor',  'Unit'),
('SWITCH-CISCO-24', 'Cisco 24-Port Network Switch',  'Network',  'Unit'),
('CHAIR-ERG',       'Ergonomic Office Chair',         'Furniture','Unit'),
('DESK-STANDING',   'Standing Desk',                 'Furniture','Unit'),
('SERVER-DELL-R740','Dell PowerEdge R740 Server',    'Server',   'Unit'),
('UPS-APC-2KVA',    'APC 2KVA UPS Unit',             'Power',    'Unit');

-- Assets
INSERT OR IGNORE INTO Assets (AssetTag, AssetName, SiteId, LocationId, SerialNumber, Category, Status, Cost, PurchaseDate, VendorId) VALUES
('TAG-0001','Dell Latitude 15 Laptop',     1, 1, 'SN-DELL-001','Laptop',   'Active',   1200.00,'2023-01-15', 1),
('TAG-0002','Dell Latitude 15 Laptop',     1, 1, 'SN-DELL-002','Laptop',   'Active',   1200.00,'2023-01-15', 1),
('TAG-0003','Dell Latitude 15 Laptop',     1, 2, 'SN-DELL-003','Laptop',   'Active',   1200.00,'2023-02-10', 1),
('TAG-0004','Lenovo ThinkPad 14',          1, 2, 'SN-LNV-001', 'Laptop',   'Active',   1100.00,'2023-02-10', 3),
('TAG-0005','Lenovo ThinkPad 14',          2, 4, 'SN-LNV-002', 'Laptop',   'Active',   1100.00,'2023-03-05', 3),
('TAG-0006','HP 24-inch Monitor',          1, 1, 'SN-HP-001',  'Monitor',  'Active',    350.00,'2023-01-15', 2),
('TAG-0007','HP 24-inch Monitor',          1, 2, 'SN-HP-002',  'Monitor',  'Active',    350.00,'2023-01-15', 2),
('TAG-0008','HP 24-inch Monitor',          2, 4, 'SN-HP-003',  'Monitor',  'Active',    350.00,'2023-03-05', 2),
('TAG-0009','Cisco 24-Port Switch',        1, 3, 'SN-CSC-001', 'Network',  'Active',   3200.00,'2022-11-20', 4),
('TAG-0010','Cisco 24-Port Switch',        3, 5, 'SN-CSC-002', 'Network',  'Active',   3200.00,'2022-12-01', 4),
('TAG-0011','Dell PowerEdge R740 Server',  1, 3, 'SN-SRV-001', 'Server',   'Active',  12000.00,'2022-06-01', 1),
('TAG-0012','Dell PowerEdge R740 Server',  1, 3, 'SN-SRV-002', 'Server',   'InRepair',12000.00,'2022-06-01', 1),
('TAG-0013','APC 2KVA UPS',               1, 3, 'SN-UPS-001', 'Power',    'Active',    800.00,'2022-06-01', 2),
('TAG-0014','Ergonomic Office Chair',      1, 1, 'SN-CHR-001', 'Furniture','Active',    450.00,'2023-04-01', 5),
('TAG-0015','Ergonomic Office Chair',      1, 2, 'SN-CHR-002', 'Furniture','Active',    450.00,'2023-04-01', 5),
('TAG-0016','Ergonomic Office Chair',      2, 4, 'SN-CHR-003', 'Furniture','Active',    450.00,'2023-04-15', 5),
('TAG-0017','Ergonomic Office Chair',      3, 5, 'SN-CHR-004', 'Furniture','Active',    450.00,'2023-05-01', 5),
('TAG-0018','Standing Desk',              1, 1, 'SN-DSK-001', 'Furniture','Active',    700.00,'2023-04-01', 5),
('TAG-0019','Standing Desk',              2, 4, 'SN-DSK-002', 'Furniture','Active',    700.00,'2023-04-15', 5),
('TAG-0020','Dell Latitude 15 Laptop',    4, 6, 'SN-DELL-004','Laptop',   'Disposed', 1200.00,'2021-01-10', 1);

-- Bills
INSERT OR IGNORE INTO Bills (VendorId, BillNumber, BillDate, DueDate, TotalAmount, Currency, Status) VALUES
(1, 'BILL-2024-001', '2024-01-10', '2024-02-10', 15600.00, 'USD', 'Paid'),
(2, 'BILL-2024-002', '2024-02-05', '2024-03-05',  2800.00, 'USD', 'Paid'),
(3, 'BILL-2024-003', '2024-03-01', '2024-04-01',  4400.00, 'USD', 'Open'),
(4, 'BILL-2024-004', '2024-03-15', '2024-04-15',  6400.00, 'USD', 'Open'),
(5, 'BILL-2024-005', '2024-04-01', '2024-05-01',  3150.00, 'USD', 'Open'),
(1, 'BILL-2024-006', '2024-04-20', '2024-05-20',  1200.00, 'USD', 'Open');

-- Purchase Orders
INSERT OR IGNORE INTO PurchaseOrders (PONumber, VendorId, PODate, Status, SiteId) VALUES
('PO-2024-001', 1, '2024-01-05', 'Closed',    1),
('PO-2024-002', 2, '2024-02-01', 'Closed',    1),
('PO-2024-003', 3, '2024-03-01', 'Approved',  2),
('PO-2024-004', 4, '2024-03-10', 'Open',      1),
('PO-2024-005', 5, '2024-04-01', 'Open',      3),
('PO-2024-006', 1, '2024-04-15', 'Open',      4);

-- PO Lines
INSERT OR IGNORE INTO PurchaseOrderLines (POId, LineNumber, ItemCode, Description, Quantity, UnitPrice) VALUES
(1, 1, 'LAPTOP-DELL-15',  'Dell Latitude 15 Laptops',     4, 1200.00),
(1, 2, 'SERVER-DELL-R740','Dell PowerEdge R740 Servers',  1,12000.00),
(2, 1, 'MONITOR-HP-24',   'HP 24-inch Monitors',          8,  350.00),
(3, 1, 'LAPTOP-LNV-14',   'Lenovo ThinkPad 14 Laptops',   4, 1100.00),
(4, 1, 'SWITCH-CISCO-24', 'Cisco 24-Port Switches',       2, 3200.00),
(5, 1, 'CHAIR-ERG',       'Ergonomic Office Chairs',       5,  450.00),
(5, 2, 'DESK-STANDING',   'Standing Desks',                2,  700.00),
(6, 1, 'LAPTOP-DELL-15',  'Dell Latitude 15 Laptop',       1, 1200.00);

-- Sales Orders
INSERT OR IGNORE INTO SalesOrders (SONumber, CustomerId, SODate, Status, SiteId) VALUES
('SO-2024-001', 1, '2024-01-20', 'Closed',   1),
('SO-2024-002', 2, '2024-02-10', 'Shipped',  1),
('SO-2024-003', 3, '2024-03-05', 'Open',     3),
('SO-2024-004', 4, '2024-03-20', 'Open',     2),
('SO-2024-005', 5, '2024-04-10', 'Open',     5);

-- SO Lines
INSERT OR IGNORE INTO SalesOrderLines (SOId, LineNumber, ItemCode, Description, Quantity, UnitPrice) VALUES
(1, 1, 'LAPTOP-DELL-15', 'Dell Latitude 15 Laptops',   2, 1500.00),
(1, 2, 'MONITOR-HP-24',  'HP 24-inch Monitors',         2,  420.00),
(2, 1, 'SWITCH-CISCO-24','Cisco 24-Port Switches',      1, 3800.00),
(3, 1, 'LAPTOP-LNV-14',  'Lenovo ThinkPad 14 Laptops',  3, 1350.00),
(4, 1, 'CHAIR-ERG',      'Ergonomic Office Chairs',      4,  550.00),
(5, 1, 'LAPTOP-DELL-15', 'Dell Latitude 15 Laptop',      1, 1500.00);

-- Asset Transactions
INSERT OR IGNORE INTO AssetTransactions (AssetId, FromLocationId, ToLocationId, TxnType, Quantity, TxnDate, Note) VALUES
(12, NULL, 3,    'Create',  1, '2022-06-01', 'Initial deployment to data center'),
(12, 3,    NULL, 'Adjust',  1, '2024-02-15', 'Sent for repair - hardware failure'),
(20, 6,    NULL, 'Dispose', 1, '2024-01-05', 'End of life - disposed per policy'),
(5,  NULL, 4,    'Move',    1, '2023-03-05', 'Deployed to Alexandria branch');
"""

_db_connection = None
_db_lock = threading.Lock()


def get_db() -> sqlite3.Connection:
    """Returns the shared in-memory SQLite connection (singleton)."""
    global _db_connection
    with _db_lock:
        if _db_connection is None:
            _db_connection = sqlite3.connect(":memory:", check_same_thread=False)
            _db_connection.row_factory = sqlite3.Row
            _db_connection.executescript(SCHEMA_SQL)
            _db_connection.executescript(SEED_SQL)
            _db_connection.commit()
    return _db_connection


def execute_query(sql: str) -> tuple[bool, list, str]:
    """
    Execute a SQL query against the in-memory SQLite DB.
    Returns (success, rows_as_dicts, error_message)
    """
    try:
        conn = get_db()
        with _db_lock:
            cursor = conn.execute(sql)
            rows = [dict(row) for row in cursor.fetchall()]
        return True, rows, ""
    except Exception as e:
        return False, [], str(e)


def get_data_summary() -> str:
    """Returns a plain-text snapshot of current data for the system prompt.
    Uses paragraphs to avoid the LLM confusing summary labels with real schema column names.
    """
    conn = get_db()
    parts = []

    with _db_lock:
        # Sites
        sites = [dict(r) for r in conn.execute(
            "SELECT SiteName, City, Country FROM Sites WHERE IsActive=1").fetchall()]
        site_list = ", ".join(f"{s['SiteName']} ({s['City']}, {s['Country']})" for s in sites)
        parts.append(f"SITES ({len(sites)} total): {site_list}")

        # Vendors
        vendors = [dict(r) for r in conn.execute(
            "SELECT VendorName, City, Country FROM Vendors WHERE IsActive=1").fetchall()]
        vendor_list = ", ".join(f"{v['VendorName']} ({v['City']}, {v['Country']})" for v in vendors)
        parts.append(f"VENDORS ({len(vendors)} total): {vendor_list}")

        # Customers
        customers = [dict(r) for r in conn.execute(
            "SELECT CustomerName, BillingCity, BillingCountry FROM Customers WHERE IsActive=1").fetchall()]
        cust_list = ", ".join(
            f"{c['CustomerName']} ({c['BillingCity']}, {c['BillingCountry']})" for c in customers)
        parts.append(f"CUSTOMERS ({len(customers)} total): {cust_list}")

        # Items
        items = [dict(r) for r in conn.execute(
            "SELECT ItemName, Category FROM Items WHERE IsActive=1").fetchall()]
        item_list = ", ".join(f"{i['ItemName']} [{i['Category']}]" for i in items)
        parts.append(f"ITEMS ({len(items)} total): {item_list}")

        # Assets — per-site, per-category, per-status
        asset_rows = [dict(r) for r in conn.execute("""
            SELECT s.SiteName, a.Category, a.Status,
                   COUNT(*) AS asset_count, ROUND(SUM(a.Cost), 2) AS total_cost
            FROM Assets a JOIN Sites s ON s.SiteId = a.SiteId
            GROUP BY s.SiteName, a.Category, a.Status
            ORDER BY s.SiteName, a.Category
        """).fetchall()]
        total_active   = sum(r['asset_count'] for r in asset_rows if r['Status'] == 'Active')
        total_inrepair = sum(r['asset_count'] for r in asset_rows if r['Status'] == 'InRepair')
        total_disposed = sum(r['asset_count'] for r in asset_rows if r['Status'] == 'Disposed')
        total_value    = sum(r['total_cost'] or 0 for r in asset_rows if r['Status'] != 'Disposed')
        asset_lines = [
            f"ASSETS — {total_active} Active, {total_inrepair} InRepair, {total_disposed} Disposed.",
            f"Total value of non-disposed assets: ${total_value:,.2f}.",
            "Breakdown (Site | Category | Status | NumberOfAssets | TotalCostUSD):"
        ]
        for r in asset_rows:
            asset_lines.append(
                f"  - {r['SiteName']} | {r['Category']} | {r['Status']} | "
                f"{r['asset_count']} assets | ${r['total_cost']:,.2f}"
            )
        parts.append("\n".join(asset_lines))

        # Assets by vendor
        vendor_asset_rows = [dict(r) for r in conn.execute("""
            SELECT v.VendorName, COUNT(*) AS asset_count
            FROM Assets a JOIN Vendors v ON v.VendorId = a.VendorId
            WHERE a.Status <> 'Disposed'
            GROUP BY v.VendorName
            ORDER BY asset_count DESC
        """).fetchall()]
        vendor_asset_lines = ["ASSETS BY VENDOR (non-disposed):"]
        for r in vendor_asset_rows:
            vendor_asset_lines.append(f"  - {r['VendorName']}: {r['asset_count']} assets")
        parts.append("\n".join(vendor_asset_lines))

        # Bills
        bills = [dict(r) for r in conn.execute(
            "SELECT BillNumber, TotalAmount, Currency, Status FROM Bills ORDER BY BillDate"
        ).fetchall()]
        open_bill_total = sum(b['TotalAmount'] for b in bills if b['Status'] == 'Open')
        bill_lines = [f"BILLS ({len(bills)} total, open total: ${open_bill_total:,.2f} USD):"]
        for b in bills:
            bill_lines.append(
                f"  - {b['BillNumber']}: ${b['TotalAmount']:,.2f} {b['Currency']} — {b['Status']}"
            )
        parts.append("\n".join(bill_lines))

        # Purchase Orders
        pos = [dict(r) for r in conn.execute(
            "SELECT PONumber, Status, PODate FROM PurchaseOrders ORDER BY PODate"
        ).fetchall()]
        open_pos = [p for p in pos if p['Status'] in ('Open', 'Approved')]
        po_lines = [f"PURCHASE ORDERS ({len(pos)} total, {len(open_pos)} open/approved):"]
        for p in pos:
            po_lines.append(f"  - {p['PONumber']} | {p['PODate']} | {p['Status']}")
        parts.append("\n".join(po_lines))

        # Sales Orders
        sos = [dict(r) for r in conn.execute(
            "SELECT SONumber, Status, SODate FROM SalesOrders ORDER BY SODate"
        ).fetchall()]
        open_sos = [s for s in sos if s['Status'] in ('Open', 'Shipped')]
        so_lines = [f"SALES ORDERS ({len(sos)} total, {len(open_sos)} open/shipped):"]
        for s in sos:
            so_lines.append(f"  - {s['SONumber']} | {s['SODate']} | {s['Status']}")
        parts.append("\n".join(so_lines))

    return "\n\n".join(parts)
