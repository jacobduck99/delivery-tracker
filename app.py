from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from sqlite3 import IntegrityError
from datetime import datetime, timezone, date, timedelta
from zoneinfo import ZoneInfo
from breaks import get_scheduled_break, handle_start_break, handle_skip_break
from time_helpers import get_iso_timestamp, attach_local_times, attach_duration_datetimes
from database import get_db, init_db, close_db, ensure_db
from time_zone import convert_timedate, convert_to_sydney, format_local_string 
from delivery_routes import start_delivery_logic, stop_delivery_logic
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from auth import User 
import os

app = Flask(__name__)
ensure_db()
app.secret_key = "a-very-secret-value"
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7) 


login_manager = LoginManager()
login_manager.login_view = "signup" #can change to login
login_manager.init_app(app)

with app.app_context():
    init_db()

app.teardown_appcontext(close_db)

@login_manager.unauthorized_handler
def unauthorized():
    flash("to access app please register or login to continue.", "error")
    return redirect(url_for("signup")) #can change to login later


@login_manager.user_loader
def load_user(user_id: str):
    print("user_loader called with:", repr(user_id))
    try:
        uid = int(user_id)
        if uid <= 0:
            return None
    except (TypeError, ValueError):
        return None
    return User.get(uid)

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    else:
        return redirect(url_for("signup"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("""
            INSERT INTO users 
            (email, password_hash)
            VALUES (?,?)
        """, (email, generate_password_hash(password),))

            conn.commit()

            user_id = cur.lastrowid

            row = conn.execute("SELECT id, email, password_hash FROM users WHERE id = ?",(user_id,)).fetchone()

            user = User.from_row(row)

            login_user(user, remember=True)

            return redirect(url_for("configuration"))

        except IntegrityError:
            flash("That email is already registered. Please log in.", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()

        conn = get_db()
        cur = conn.cursor()
        row = cur.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email,)).fetchone()

        if row is None:
            flash("No account found")
            return render_template("login.html")

        user = User.from_row(row)

        password = request.form.get("password")

        if not check_password_hash(user.password_hash, password):
            flash("Wrong email/password")
            return render_template("login.html")

        login_user(user, remember=True)
        return redirect(url_for("configuration"))
            
    return render_template("login.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    session.clear()
    resp = redirect(url_for("login"))
    resp.delete_cookie("remember_token")
    resp.delete_cookie("session")
    return resp


@app.route("/configuration", methods=["GET", "POST"])
@login_required
def configuration():
    if request.method == "POST":

        van_name = (request.form.get("van_name") or "").strip()
        van_num_raw = (request.form.get("van_number") or "").strip()
        drops_raw = (request.form.get("num_drops") or "").strip()

        # optional short text -> NULL if blank, trim spaces
        truck_damage = ((request.form.get("truck_damage") or "").strip()) or None
        if truck_damage and len(truck_damage) > 255:
            flash("Truck damage must be 255 characters or less")
            return redirect(url_for("configuration"))
 
        if not van_name:
            flash("Van name is required")
            return redirect(url_for("configuration"))

        try:
            van_num = int(van_num_raw)
        except ValueError:
            flash("Van number must be a whole number")
            return redirect(url_for("configuration"))

        try:
            drops = int(drops_raw)
        except ValueError:
            flash("Number of drops must be a whole number")
            return redirect(url_for("configuration"))

        # ---- timestamps (start/first/second are NOT NULL in schema) ----
        start_ts = get_iso_timestamp("shift_start")
        first_break_ts = get_iso_timestamp("first_break")
        second_break_ts = get_iso_timestamp("second_break")
        end_ts = get_iso_timestamp("shift_end")  # nullable

        if not (start_ts and first_break_ts and second_break_ts):
            flash("Start time and both break times are required")
            return redirect(url_for("configuration"))

        user_id = current_user.id  # ensure this matches users.id

        # ---- insert ----
        conn = get_db()
        # make sure PRAGMA foreign keys is ON in get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO run
              (user_id, van_number, van_name, start_time, first_break, second_break,
               end_time, number_of_drops, truck_damage)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (user_id, van_num, van_name, start_ts, first_break_ts, second_break_ts,
             end_ts, drops, truck_damage),
        )
        conn.commit()

        session["run_id"] = cur.lastrowid
        session["num_drops"] = drops
        return redirect(url_for("index"))

    return render_template("configuration.html", user=current_user)



@app.route("/index", methods=["GET"])
@login_required
def index():
    conn = get_db()
    run_id = session.get("run_id")

    # how many drops did we set up?
    run = conn.execute(
        "SELECT number_of_drops FROM run WHERE id = ?", (run_id,)
    ).fetchone()
    num_drops = run["number_of_drops"] if run else 0

    # fetch raw rows
    rows = conn.execute(
        """
        SELECT drop_idx, start_ts, end_ts, elapsed
        FROM deliveries
        WHERE run_id = ?
        ORDER BY drop_idx
        """,
        (run_id,),
    ).fetchall()

    # turn each sqlite3.Row into a dict & attach local times
    deliveries = attach_local_times(rows)
    
    return render_template(
        "index.html",
        num_drops=num_drops,
        deliveries=deliveries,
    )

@app.route("/deliveries", methods=["POST"])
@login_required
def start_delivery():
    action = request.form.get("action")
    drop_idx = int(request.form["drop_index"])
    run_id = session["run_id"]

    if action == "start":
        return start_delivery_logic(run_id, drop_idx)
    elif action == "stop":
        return stop_delivery_logic(run_id, drop_idx)

    return redirect(url_for("index", _anchor=f"drop-{drop_idx}")) 

@app.route("/breaks", methods=["POST"])
@login_required
def breaks():
    action = request.form.get("action")
    break_number = int(request.form.get("break_number"))

    conn = get_db()
    cur = conn.cursor()

    scheduled_time_str = get_scheduled_break(cur, session["run_id"], break_number)
    if not scheduled_time_str:
        return redirect(url_for("index"))  # or handle error

    if action == "start_break":
        handle_start_break(cur, session["run_id"], break_number, scheduled_time_str)
        conn.commit()

    elif action == "skip_break":
        handle_skip_break(cur, session["run_id"], break_number)
        conn.commit()

    return redirect(url_for("index"))


@app.route("/pastruns")
@login_required
def past_runs():
    conn = get_db()
    raw_runs = conn.execute(
        "SELECT * FROM run WHERE user_id = ? ORDER BY start_time DESC, id DESC",
        (current_user.id,)
    ).fetchall()

    runs = attach_local_times(raw_runs)   # [] is fine
    attach_duration_datetimes(runs)       # safely no-ops on []

    if not runs:
        flash("No runs recorded. Please complete a shift to access history data", "info")

    return render_template("past_runs.html", runs=runs)


@app.route("/stats") #current run info
@login_required
def stats():
    conn = get_db()
    run_id = session.get("run_id")
    if run_id is None:
        flash("No active run. Start a run first.", "info")
        return redirect(url_for("configuration"))

    run_row = conn.execute("SELECT * FROM run WHERE id = ? AND user_id = ?",(run_id, current_user.id)).fetchone()

    if not run_row:
        session.pop("run_id", None)
        flash("No active run. Start a run first.", "info")
        return redirect(url_for("configuration"))
        
    run = dict(run_row)
    run = attach_local_times([run])[0] 
    attach_duration_datetimes([run])

    drops = conn.execute("SELECT * FROM deliveries WHERE run_id = ? ORDER BY drop_idx", (run_id,)).fetchall()

    return render_template("stats.html", run=run, drops=drops)


@app.route("/reset-db")
def reset_db():
    conn = get_db()
    cur = conn.cursor()

    # DROP old tables
    cur.execute("DROP TABLE IF EXISTS deliveries;")
    cur.execute("DROP TABLE IF EXISTS breaks;")
    cur.execute("DROP TABLE IF EXISTS run;")

    # CREATE new schema
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS run (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      van_number      INTEGER NOT NULL,
      van_name        TEXT    NOT NULL,
      start_time      TEXT    NOT NULL,
      first_break     TEXT    NOT NULL,
      second_break    TEXT    NOT NULL,
      end_time        TEXT,
      number_of_drops INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS deliveries (
      id        INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id    INTEGER NOT NULL,
      drop_idx  INTEGER NOT NULL,
      start_ts  TEXT,
      end_ts    TEXT,
      elapsed   INTEGER,
      expected_minutes REAL,
      status    TEXT,
      FOREIGN KEY (run_id) REFERENCES run(id)
    );

    CREATE TABLE IF NOT EXISTS breaks (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id          INTEGER NOT NULL,
      break_number    INTEGER NOT NULL,
      scheduled_time  TEXT    NOT NULL,
      actual_time     TEXT,
      late_minutes    INTEGER,
      status          TEXT,
      FOREIGN KEY (run_id) REFERENCES run(id),
      UNIQUE (run_id, break_number)
    );
    """)

    conn.commit()
    return "Database reset with new schema!"



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # <- use Fly's PORT
    app.run(host="0.0.0.0", port=port, debug=True)

