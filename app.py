from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
from breaks import get_scheduled_break, handle_start_break, handle_skip_break
from time_helpers import get_iso_timestamp
from time_helpers import attach_local_times

from database import get_db, init_db, close_db
from time_zone import convert_timedate, convert_to_sydney 
app = Flask(__name__)
app.secret_key = "a-very-secret-value"

with app.app_context():
    init_db()

app.teardown_appcontext(close_db)

SYDNEY = ZoneInfo("Australia/Sydney")


@app.route("/configuration", methods=["GET", "POST"])
def configuration():
    if request.method == "POST":
        van_num = request.form.get("van_number")
        van_name = request.form.get("van_name")

        start_ts = get_iso_timestamp("shift_start") 
        first_break_ts = get_iso_timestamp("first_break")
        second_break_ts = get_iso_timestamp("second_break")
        end_ts = get_iso_timestamp("shift_end")

        drops = int(request.form.get("num_drops"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO run
              (van_number, van_name, start_time, first_break, second_break,
              end_time, number_of_drops)
            VALUES (?,?,?,?,?,?,?)
            """,
            (van_num, van_name, start_ts, first_break_ts, second_break_ts, end_ts, drops),
        )
        new_id = cur.lastrowid



        conn.commit()

        
        session["run_id"] = new_id
        session["num_drops"] = drops

        return redirect(url_for("index"))

    return render_template("configuration.html")


@app.route("/", methods=["GET"])
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
def start_delivery():
    action = request.form.get("action")
    drop_idx = int(request.form["drop_index"])

    conn = get_db()
    cur = conn.cursor()

    if action == "start":
        # record UTC start
        start_utc = datetime.now(timezone.utc)
        start_ts = start_utc.isoformat()
        cur.execute(
            "INSERT INTO deliveries(run_id, drop_idx, start_ts) VALUES (?,?,?)",
            (session["run_id"], drop_idx, start_ts),
        )
        conn.commit()
        return redirect(url_for("index", _anchor=f"drop-{drop_idx}"))

    elif action == "stop":
        # record UTC end
        end_utc = datetime.now(timezone.utc)
        end_ts = end_utc.isoformat()


        # fetch the original start_ts
        row = cur.execute(
            """
            SELECT start_ts
            FROM deliveries
            WHERE run_id = ? AND drop_idx = ?
            """,
            (session["run_id"], drop_idx),
        ).fetchone()
        start_ts = row["start_ts"]

        # compute elapsed
        end_dt = datetime.fromisoformat(end_ts)
        start_dt = datetime.fromisoformat(start_ts)
        elapsed = end_dt - start_dt
        pretty_elapsed = str(elapsed).split(".")[0]

        # update
        cur.execute(
            """
            UPDATE deliveries
            SET end_ts = ?, elapsed = ?
            WHERE run_id = ? AND drop_idx = ?
            """,
            (end_ts, pretty_elapsed, session["run_id"], drop_idx),
        )
        conn.commit()
        return redirect(url_for("index", _anchor=f"drop-{drop_idx}"))
    


@app.route("/breaks", methods=["POST"])
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





@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("configuration"))


@app.route("/past_runs")
def past_runs():
    conn = get_db()
    runs = conn.execute("SELECT * FROM run ORDER BY id DESC").fetchall()
    return render_template("past_runs.html", runs=runs)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
