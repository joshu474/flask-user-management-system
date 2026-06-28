import sqlite3

# ✅ Connect to the database
db = sqlite3.connect("users.db")

# ✅ Create a cursor
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# ✅ Execute a query
cursor.execute("SELECT username, password FROM users")

# ✅ Fetch all rows
for row in cursor.fetchall():
    print(f"[{row[0]}]")

# ✅ Close connection
db.close()
