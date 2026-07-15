import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS users_new")

conn.commit()
conn.close()

print("Empty users_new table removed.")