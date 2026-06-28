import sqlite3
db = sqlite3.connect("users.db")
cursor = db.cursor()
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
for user in users:
    print(user)
    db.close