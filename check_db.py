import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("SELECT username, password FROM users")
rows = cursor.fetchall()

for u, p in cursor.fetchall():
    print(u, "_>", p)

conn.close()