import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute(
    "UPDATE users SET role=? WHERE username=?",
    ("admin", "Joshua Dan")
)

conn.commit()

if cursor.rowcount > 0:
    print("Joshua Dan is now an administrator.")
else:
    print("Username not found.")

conn.close()