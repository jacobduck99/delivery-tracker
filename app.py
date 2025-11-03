from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, make_response, jsonify, request
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
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=365) 
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# before routes
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-please-change"),
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,      # False for http://192.168...
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SECURE=False,     # False for http://192.168...
)

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
            session.permanent = True

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
        session.permanent = True
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
        session.permanent = True
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
        return render_template("stats.html")

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

@app.route("/sw.js")
def sw():
    resp = make_response(send_from_directory("static", "sw.js"))
    resp.headers["Content-Type"] = "application/javascript"
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@app.route("/offline.html")
def offline():
    return send_from_directory("static", "offline.html")


@app.route('/api/drop', methods=['POST'])
def save_drop():
    if not request.is_json:
        return jsonify({"ok": False, "error": "Expected JSON"}), 400

    data = request.get_json()

    drop_index = data.get("drop_index")
    start_ts = data.get("start_ts")
    stop_ts = data.get("stop_ts")
    duration_ms = data.get("duration_ms")
    run_id = session.get("run_id")

    if not run_id:
        return jsonify({"ok": False, "error": "No run active"}), 400

    if not isinstance(drop_index, int) or start_ts is None or stop_ts is None:
        return jsonify({"ok": False, "error": "Missing or invalid fields"}), 400

    conn = get_db()
    conn.execute("""
        INSERT INTO deliveries (run_id, drop_idx, start_ts, end_ts, elapsed)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(run_id, drop_idx) DO UPDATE SET
            start_ts = excluded.start_ts,
            end_ts   = excluded.end_ts,
            elapsed  = excluded.elapsed
    """, (run_id, drop_index, start_ts, stop_ts, duration_ms))
    conn.commit()

    return jsonify({"ok": True})

@app.route('/api/run/end', methods=['POST'])
def end_run():
    user_id = current_user.id
    run_id = session.get("run_id")
    if not run_id:
        return jsonify({"ok": False, "error": "No run active"}), 400

    # optional telemetry; not used for truth
    _ = request.get_json(silent=True) or {}

    conn = get_db()
    # If your connection doesn't use Row factory, access by index [0]/[1]
    row = conn.execute(
        "SELECT start_time, actual_end_time_at FROM run WHERE id = ? AND user_id = ?",
        (run_id, user_id)
    ).fetchone()

    if row is None:
        return jsonify({"ok": False, "error": "RUN_NOT_FOUND_OR_NOT_OWNED"}), 404

    # already ended? return idempotently
    if row["actual_end_time_at"] is not None:
        start_dt  = datetime.fromisoformat(row["start_time"])
        end_dt    = datetime.fromisoformat(row["actual_end_time_at"])
        duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
        return jsonify({
            "ok": True,
            "run_id": run_id,
            "actual_end_time_at": end_dt.isoformat(),
            "duration_ms": duration_ms
        })

    # stamp end now (server UTC) and compute duration
    end_dt   = datetime.now(timezone.utc)
    start_dt = datetime.fromisoformat(row["start_time"])
    duration_ms = int((end_dt - start_dt).total_seconds() * 1000)

    conn.execute(
        "UPDATE run SET actual_end_time_at = ?, duration_ms = ? WHERE id = ? AND user_id = ?",
        (end_dt.isoformat(), duration_ms, run_id, user_id)
    )
    conn.commit()

    # (optional) session pop so a new run must be created next time
    # session.pop("run_id", None)

    return jsonify({
        "ok": True,
        "run_id": run_id,
        "actual_end_time_at": end_dt.isoformat(),
        "duration_ms": duration_ms
    })

@app.template_filter("fmt_duration")
def fmt_duration(value):
    try:
        ms = int(value)
    except (TypeError, ValueError):
        return "0:00"
    secs = ms // 1000
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # <- use Fly's PORT
    app.run(host="0.0.0.0", port=port, debug=True)

