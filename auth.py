from flask_login import UserMixin
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from database import get_db, init_db, close_db

class User(UserMixin):
    def __init__(self, id, email, password_hash):
        self.id = str(id)
        self.email = email
        self.password_hash = password_hash
    
    @classmethod
    def from_row(cls, row):
        return cls(row["id"], row["email"], row["password_hash"])

    @staticmethod
    def get(user_id: str):
        if not user_id:
            return None
        try:
            conn = get_db()
            row = conn.execute(
                "SELECT id, email, password_hash FROM users WHERE id = ?",
                (int(user_id),)
            ).fetchone()
            return User.from_row(row) if row else None
        except (ValueError, TypeError):
        # If cast fails or no such row → not logged in
            return None

