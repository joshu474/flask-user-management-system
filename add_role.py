import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'"
    )
    print("Role column added successfully.")
except sqlite3.OperationalError as e:
    print(e)

conn.commit()
conn.close()
