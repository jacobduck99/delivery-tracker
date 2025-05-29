from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from database import get_db, init_db, close_db

app = Flask(__name__)
app.secret_key = "a-very-secret-value"

with app.app_context():
    init_db()

app.teardown_appcontext(close_db)

SYDNEY = ZoneInfo("Australia/Sydney")


@app.route("/configuration", methods=["GET", "POST"])
def configuration():
    if request.method == "POST":
        van = request.form.get("van_number")
        start = request.form.get("shift_start")
        end = request.form.get("shift_end")
        drops = int(request.form.get("num_drops"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO run
              (van_number, start_time, end_time, number_of_drops)
            VALUES (?,?,?,?)
            """,
            (van, start, end, drops),
        )
        conn.commit()

        new_id = cur.lastrowid
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
    deliveries = []
    for row in rows:
        d = dict(row)
        if d.get("start_ts"):
            start_utc = datetime.fromisoformat(d["start_ts"]).replace(
                tzinfo=timezone.utc
            )
            d["start_local"] = start_utc.astimezone(SYDNEY)
        if d.get("end_ts"):
            end_utc = datetime.fromisoformat(d["end_ts"]).replace(
                tzinfo=timezone.utc
            )
            d["end_local"] = end_utc.astimezone(SYDNEY)
        deliveries.append(d)

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
        start_ts = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "INSERT INTO deliveries(run_id, drop_idx, start_ts) VALUES (?,?,?)",
            (session["run_id"], drop_idx, start_ts),
        )
        conn.commit()
        return redirect(url_for("index"))

    elif action == "stop":
        # record UTC end
        end_ts = datetime.now(timezone.utc).isoformat()

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
        end_dt = datetime.fromisoformat(end_ts).replace(tzinfo=timezone.utc)
        start_dt = datetime.fromisoformat(start_ts).replace(tzinfo=timezone.utc)
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
    app.run(host="0.0.0.0", port=5000, debug=False)
