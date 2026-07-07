"""Create / refresh the business SQLite database (data/demo.db).

Do not confuse with data/chat.db:
- data/chat.db     — sessions / messages (FastAPI persistence)
- data/demo.db     — business demo data for npi_db_agent

Skills live under skills/*/SKILL.md and are loaded by Agent at runtime.
Usage (from project root, after ``pip install -e .``):
    python scripts/demo_db.py
    multi-agent-init-demo
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from subagent.config.paths import resolve_demo_db_path


def create_demo_db(db_path: str | Path | None = None) -> None:
    """Drop & recreate business tables with richer sample data."""
    path = resolve_demo_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.executescript(
        """
        PRAGMA foreign_keys = OFF;
        DROP TABLE IF EXISTS inventory_movements;
        DROP TABLE IF EXISTS payments;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS product_suppliers;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS categories;
        DROP TABLE IF EXISTS suppliers;
        DROP TABLE IF EXISTS customers;
        PRAGMA foreign_keys = ON;

        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );

        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            contact_name TEXT,
            phone TEXT,
            city TEXT
        );

        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            sku TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            stock_qty INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE product_suppliers (
            product_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            supply_price REAL NOT NULL,
            is_primary INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (product_id, supplier_id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            city TEXT,
            tier TEXT NOT NULL DEFAULT 'standard',
            join_date TEXT NOT NULL
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            shipping_city TEXT,
            note TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_amount REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE payments (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            pay_method TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_at TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        CREATE TABLE inventory_movements (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            delta_qty INTEGER NOT NULL,
            reason TEXT NOT NULL,
            ref_order_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (ref_order_id) REFERENCES orders(id)
        );
        """
    )

    categories = [
        (1, "Electronics", "电子数码"),
        (2, "Furniture", "办公家具"),
        (3, "Accessories", "配件周边"),
    ]
    cur.executemany("INSERT INTO categories VALUES (?,?,?)", categories)

    suppliers = [
        (1, "华东数码供应", "王经理", "021-88880001", "上海"),
        (2, "京联办公", "李主管", "010-66660002", "北京"),
        (3, "深创配件", "陈小姐", "0755-77770003", "深圳"),
    ]
    cur.executemany("INSERT INTO suppliers VALUES (?,?,?,?,?)", suppliers)

    products = [
        (1, "E-LAP-001", "Laptop", 1, 5999.0, 42, "active"),
        (2, "E-MOU-002", "Mouse", 1, 99.0, 200, "active"),
        (3, "E-KEY-003", "Keyboard", 1, 299.0, 85, "active"),
        (4, "F-CHA-004", "Chair", 2, 899.0, 30, "active"),
        (5, "F-DSK-005", "Desk", 2, 1599.0, 18, "active"),
        (6, "E-MON-006", "Monitor", 1, 1999.0, 55, "active"),
        (7, "E-HDP-007", "Headphones", 1, 599.0, 120, "active"),
        (8, "E-CAM-008", "Webcam", 1, 299.0, 90, "active"),
        (9, "A-USB-009", "USB Hub", 3, 129.0, 150, "active"),
        (10, "A-PAD-010", "Mouse Pad", 3, 49.0, 300, "discontinued"),
    ]
    cur.executemany("INSERT INTO products VALUES (?,?,?,?,?,?,?)", products)

    product_suppliers = [
        (1, 1, 5200.0, 1),
        (2, 1, 65.0, 1),
        (3, 1, 210.0, 1),
        (4, 2, 720.0, 1),
        (5, 2, 1280.0, 1),
        (6, 1, 1750.0, 1),
        (7, 3, 420.0, 1),
        (8, 3, 210.0, 1),
        (9, 3, 85.0, 1),
    ]
    cur.executemany("INSERT INTO product_suppliers VALUES (?,?,?,?)", product_suppliers)

    customers = [
        (1, "Zhang San", "zhang@example.com", "Shanghai", "gold", "2024-01-15"),
        (2, "Li Si", "li@example.com", "Beijing", "standard", "2024-02-20"),
        (3, "Wang Wu", "wang@example.com", "Shanghai", "silver", "2024-03-10"),
        (4, "Zhao Liu", "liu@example.com", "Guangzhou", "standard", "2024-04-05"),
        (5, "Chen Qi", "chen@example.com", "Shenzhen", "gold", "2024-05-12"),
        (6, "Sun Ba", "sun@example.com", "Hangzhou", "standard", "2024-06-01"),
    ]
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", customers)

    orders = [
        (1, 1, "2025-01-15", "completed", "Shanghai", None),
        (2, 1, "2025-01-16", "completed", "Shanghai", "加急"),
        (3, 2, "2025-02-10", "completed", "Beijing", None),
        (4, 2, "2025-02-15", "completed", "Beijing", None),
        (5, 3, "2025-03-05", "completed", "Shanghai", None),
        (6, 3, "2025-03-20", "cancelled", "Shanghai", "客户取消"),
        (7, 4, "2025-03-25", "completed", "Guangzhou", None),
        (8, 4, "2025-04-01", "completed", "Guangzhou", None),
        (9, 5, "2025-04-10", "completed", "Shenzhen", None),
        (10, 5, "2025-04-15", "shipped", "Shenzhen", None),
        (11, 1, "2025-04-20", "completed", "Shanghai", None),
        (12, 2, "2025-05-01", "pending", "Beijing", "等待付款"),
        (13, 6, "2025-05-08", "completed", "Hangzhou", "新品"),
    ]
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders)

    order_items = [
        (1, 1, 1, 1, 5999.0, 5999.0),
        (2, 2, 2, 2, 99.0, 198.0),
        (3, 3, 3, 1, 299.0, 299.0),
        (4, 4, 5, 1, 1599.0, 1599.0),
        (5, 5, 6, 2, 1999.0, 3998.0),
        (6, 6, 7, 1, 599.0, 599.0),
        (7, 7, 1, 1, 5999.0, 5999.0),
        (8, 8, 4, 2, 899.0, 1798.0),
        (9, 9, 8, 3, 299.0, 897.0),
        (10, 10, 2, 5, 99.0, 495.0),
        (11, 11, 3, 1, 299.0, 299.0),
        (12, 12, 6, 1, 1999.0, 1999.0),
        (13, 13, 9, 2, 129.0, 258.0),
        (14, 13, 2, 1, 99.0, 99.0),
        (15, 5, 7, 1, 599.0, 599.0),
    ]
    cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?,?)", order_items)

    payments = [
        (1, 1, "alipay", 5999.0, "2025-01-15 10:00", "paid"),
        (2, 2, "wechat", 198.0, "2025-01-16 14:20", "paid"),
        (3, 3, "card", 299.0, "2025-02-10 09:15", "paid"),
        (4, 4, "alipay", 1599.0, "2025-02-15 16:40", "paid"),
        (5, 5, "card", 3998.0, "2025-03-05 11:00", "paid"),
        (6, 6, "wechat", 599.0, "2025-03-20 08:30", "refunded"),
        (7, 7, "alipay", 5999.0, "2025-03-25 19:00", "paid"),
        (8, 8, "card", 1798.0, "2025-04-01 12:10", "paid"),
        (9, 9, "wechat", 897.0, "2025-04-10 20:00", "paid"),
        (10, 11, "alipay", 299.0, "2025-04-20 15:30", "paid"),
        (11, 13, "alipay", 357.0, "2025-05-08 10:05", "paid"),
    ]
    cur.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?)", payments)

    inventory_movements = [
        (1, 1, -1, "sale", 1, "2025-01-15 10:00"),
        (2, 2, -2, "sale", 2, "2025-01-16 14:20"),
        (3, 1, 50, "purchase", None, "2025-01-01 09:00"),
        (4, 6, -2, "sale", 5, "2025-03-05 11:00"),
        (5, 7, 30, "purchase", None, "2025-02-01 09:00"),
        (6, 9, -2, "sale", 13, "2025-05-08 10:05"),
        (7, 10, -5, "adjustment", None, "2025-04-01 00:00"),
    ]
    cur.executemany(
        "INSERT INTO inventory_movements VALUES (?,?,?,?,?,?)",
        inventory_movements,
    )

    conn.commit()
    conn.close()

    tables = [
        "categories",
        "suppliers",
        "products",
        "product_suppliers",
        "customers",
        "orders",
        "order_items",
        "payments",
        "inventory_movements",
    ]
    print(f"Business database created: {path}")
    print(f"Tables ({len(tables)}): {', '.join(tables)}")
    print("Note: chat history is in data/chat.db (not this file).")


def main() -> None:
    create_demo_db()


if __name__ == "__main__":
    main()
