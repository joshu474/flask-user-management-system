import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

for username, password in users:
    if not password.startswith("scrypt:"):
        hashed = generate_password_hash(password)
 
        cursor.execute(
        "UPDATE users SET password=? WHERE username=?",
        (hashed, username)
    )

conn.commit()
conn.close()

print("All passwords converted to hashed format.")