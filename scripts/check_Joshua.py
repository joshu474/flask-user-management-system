import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM users_new")
print("Rows in users_new:", cursor.fetchone()[0])

cursor.execute("PRAGMA table_info(users_new)")
print("\nSchema:")
for row in cursor.fetchall():
    print(row)

conn.close()