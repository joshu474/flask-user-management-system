import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

print("Old table:")
cursor.execute("SELECT COUNT(*) FROM users")
print(cursor.fetchone()[0])

print("\nNew table:")
cursor.execute("SELECT COUNT(*) FROM users_new")
print(cursor.fetchone()[0])

print("\nSample rows from users_new:")
cursor.execute("""
SELECT id, username, role, active
FROM users_new
ORDER BY id
""")

for row in cursor.fetchall():
    print(row)

conn.close()