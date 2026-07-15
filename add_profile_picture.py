import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
ALTER TABLE users
ADD COLUMN profile_picture TEXT
""")

conn.commit()
conn.close()

print("profile_picture column added.")
