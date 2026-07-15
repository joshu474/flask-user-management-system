import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create the new table
cursor.execute("""
CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
)
""")

# Read all users from the old table
cursor.execute("SELECT username, password, role FROM users")
old_users = cursor.fetchall()

print("Users found in old table:", len(old_users))

# Copy one user at a time
for user in old_users:
    cursor.execute(
        """
        INSERT INTO users_new (username, password, role)
        VALUES (?, ?, ?)
        """,
        user
    )

conn.commit()

# Verify the copy
cursor.execute("SELECT COUNT(*) FROM users_new")
print("Users copied:", cursor.fetchone()[0])

conn.close()

print("Database upgrade completed successfully.")
