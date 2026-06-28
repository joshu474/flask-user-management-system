import sqlite3

db = sqlite3.connect("users.db")
cursor = db.cursor()

# Insert a new user
cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("joshua", "1234"))

db.commit()
db.close()

print("User added successfully!")
