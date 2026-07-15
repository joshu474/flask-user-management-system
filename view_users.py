import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")

for column in cursor.fetchall():
    print(column)

conn.close()
