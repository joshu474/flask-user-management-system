import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create the new table
cursor.execute("""
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    email TEXT,
    created_at TEXT,
    profile_picture TEXT,
    active INTEGER NOT NULL DEFAULT 1
)
""")

# Copy all users
cursor.execute("""
INSERT INTO users_new
(username, password, role, email, created_at, profile_picture, active)
SELECT
username, password, role, email, created_at, profile_picture, active
FROM users
""")

conn.commit()

print("Migration completed successfully.")

conn.close()
