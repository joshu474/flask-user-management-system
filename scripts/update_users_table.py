import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN failed_attempts INTEGER DEFAULT 0
    """)
    print("failed_attempts column added.")
except Exception:
    print("failed_attempts column already exists.")

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN locked_until TEXT
    """)
    print("locked_until column added.")
except Exception:
    print("locked_until column already exists.")

conn.commit()
conn.close()

print("Database updated successfully.")
