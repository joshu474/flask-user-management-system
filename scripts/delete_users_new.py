import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE users_new")

conn.commit()
conn.close()

print("users_new deleted successfully.")
