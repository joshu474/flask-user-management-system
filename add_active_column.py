import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN active INTEGER DEFAULT 1
    """)
    print("Active column added successfully.")
except sqlite3.OperationalError:
    print("Active column already exists.")

conn.commit()
conn.close()
