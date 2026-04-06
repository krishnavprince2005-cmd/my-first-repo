import sqlite3
import hashlib

DB_FILE = 'finance.db'

def create_table():
    """Create the initial table to store transactions if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            amount REAL,
            category TEXT,
            type TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            user_id INTEGER,
            month TEXT,
            category TEXT,
            amount_limit REAL,
            PRIMARY KEY (user_id, month, category)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            name TEXT PRIMARY KEY
        )
    ''')

    # Migration for transactions
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER DEFAULT 1")

    # Migration for budgets
    cursor.execute("PRAGMA table_info(budgets)")
    columns_b = [col[1] for col in cursor.fetchall()]
    if "user_id" not in columns_b:
        cursor.execute("ALTER TABLE budgets RENAME TO old_budgets")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                user_id INTEGER,
                month TEXT,
                category TEXT,
                amount_limit REAL,
                PRIMARY KEY (user_id, month, category)
            )
        ''')
        cursor.execute("INSERT INTO budgets (user_id, month, category, amount_limit) SELECT 1, month, category, amount_limit FROM old_budgets")
        cursor.execute("DROP TABLE old_budgets")
    
    # Pre-populate categories if empty
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] == 0:
        default_categories = ["Salary", "Food", "Rent", "Utilities", "Entertainment", "Other"]
        cursor.executemany('INSERT INTO categories (name) VALUES (?)', [(c,) for c in default_categories])
        
    conn.commit()
    conn.close()

def add_transaction(user_id, date, description, amount, category, t_type):
    """Insert a new transaction into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, date, description, amount, category, type)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, date, description, amount, category, t_type))
    conn.commit()
    conn.close()

def get_all_transactions(user_id):
    """Fetch all stored transactions for a given user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_transaction(transaction_id, user_id):
    """Remove a transaction by its ID for a specific user."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, user_id))
    conn.commit()
    conn.close()

def set_budget(user_id, month, category, amount_limit):
    """Set the budget limit for a specific user, month and category."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO budgets (user_id, month, category, amount_limit)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, month, category) DO UPDATE SET amount_limit=excluded.amount_limit
    ''', (user_id, month, category, amount_limit))
    conn.commit()
    conn.close()

def get_budget(user_id, month, category):
    """Get the budget limit for a specific month and category. Returns None if not set."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT amount_limit FROM budgets WHERE user_id = ? AND month = ? AND category = ?', (user_id, month, category))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def update_transaction(transaction_id, user_id, date, description, amount, category, t_type):
    """Update an existing transaction."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transactions
        SET date = ?, description = ?, amount = ?, category = ?, type = ?
        WHERE id = ? AND user_id = ?
    ''', (date, description, amount, category, t_type, transaction_id, user_id))
    conn.commit()
    conn.close()

def get_all_categories():
    """Fetch all defined categories."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM categories ORDER BY name')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_category(name):
    """Add a new category."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Already exists
    conn.close()

def delete_category(name):
    """Delete a category."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM categories WHERE name = ?', (name,))
    conn.commit()
    conn.close()

def register_user(username, password):
    """Register a new user. Returns True if successful, False if username exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, pwd_hash))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def authenticate_user(username, password):
    """Authenticate a user. Returns user_id if successful, None otherwise."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?', (username, pwd_hash))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
