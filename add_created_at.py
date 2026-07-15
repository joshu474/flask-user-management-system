import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
ALTER TABLE users
ADD COLUMN created_at TEXT
""")

conn.commit()
conn.close()

print("created_at column added successfully.")
