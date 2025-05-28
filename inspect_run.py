# inspect_run.py
import sqlite3

conn = sqlite3.connect("database.db")

print("Columns:")
for col in conn.execute("PRAGMA table_info(run)"):
    print(" ", col)

print("\nData:")
for row in conn.execute("SELECT * FROM run ORDER BY id DESC"):
    print(" ", row)

conn.close()
