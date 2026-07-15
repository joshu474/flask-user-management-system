import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    conn.commit()
    print("Email column added successfully.")
except sqlite3.OperationalError as e:
    print(e)

conn.close()
