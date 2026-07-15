import sqlite3
from datetime import datetime

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

today = datetime.now().strftime("%Y-%m-%d")

cursor.execute("""
UPDATE users
SET created_at = ?
WHERE created_at IS NULL
""", (today,))

conn.commit()
conn.close()

print("Existing users updated successfully.")
