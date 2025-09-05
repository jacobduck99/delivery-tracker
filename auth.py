from flask_login import UserMixin
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from databsae import get_db, init_db, close_db

class user(UserMixin):
    def __init__(self, id, email, password_hash):
        self.id = id
        self.email = email
        self.password_hash = password_hash

