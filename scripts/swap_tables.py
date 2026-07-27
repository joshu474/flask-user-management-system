import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Keep the old table as a backup
cursor.execute("ALTER TABLE users RENAME TO users_old")

# Make the new table live
cursor.execute("ALTER TABLE users_new RENAME TO users")

conn.commit()
conn.close()

print("Database upgraded successfully.")
