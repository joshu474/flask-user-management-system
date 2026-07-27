import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute(
    "SELECT username, active FROM users WHERE LOWER(username)=?",
    ("susan",)
)

print(cursor.fetchone())

conn.close()
