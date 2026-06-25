import sqlite3
import os

def create_database():
    # Database file path
    db_path = 'db.sqlite3'
    
    # Connect to SQLite database (this creates the file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Users Table (For Role-Based Login System)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Admin', 'Cashier'))
    )
    ''')

    # 2. Categories Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')

    # 3. Products Table (Inventory Management)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        buy_price REAL NOT NULL,
        sell_price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL,
        low_stock_threshold INTEGER DEFAULT 5,
        FOREIGN KEY (category_id) REFERENCES Categories(id)
    )
    ''')

    # 4. Customers Table (Customer CRM)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE
    )
    ''')

    # 5. Sales Table (For tracking transactions)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        user_id INTEGER,
        total_amount REAL NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES Customers(id),
        FOREIGN KEY (user_id) REFERENCES Users(id)
    )
    ''')

    # 6. Sales Items Table (For tracking individual products in a sale)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sales_Items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price_at_time REAL NOT NULL,
        FOREIGN KEY (sale_id) REFERENCES Sales(id),
        FOREIGN KEY (product_id) REFERENCES Products(id)
    )
    ''')

    # 7. Expenses Table (Expense & Profit Tracker)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 8. API Settings Table (For AI API Key storage)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS API_Settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider TEXT UNIQUE NOT NULL,
        api_key TEXT NOT NULL
    )
    ''')

    # Insert a default Admin user if none exists
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        # NOTE: In a real app, hash the password! For simplicity here, we use plain text 'admin123'
        cursor.execute("INSERT INTO Users (username, password, role) VALUES ('admin', 'admin123', 'Admin')")
        cursor.execute("INSERT INTO Users (username, password, role) VALUES ('cashier', 'cashier123', 'Cashier')")
        print("Default users created: admin/admin123 (Admin) and cashier/cashier123 (Cashier)")

    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database setup complete! Tables created in {db_path}")

if __name__ == '__main__':
    create_database()
