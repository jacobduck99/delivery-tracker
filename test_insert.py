
from app import app                       # <-- adjust import/module name

from database import get_db, init_db, close_db
             # <-- adjust import path
from werkzeug.security import generate_password_hash

def signup():
    email = input("Please add email: ")
    password = input("Please enter a password: ")

    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, generate_password_hash(password)),
        )
        conn.commit()
        print("✅ User inserted!")

if __name__ == "__signup__":
    signup()
