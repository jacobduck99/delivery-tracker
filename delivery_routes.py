from datetime import datetime, timezone
from time_helpers import attach_local_times
from flask import session, redirect, url_for
from database import get_db
from time_zone import convert_to_sydney

def start_delivery_logic(run_id, drop_idx):
    conn = get_db()
    cur = conn.cursor()
    start_ts = datetime.now(timezone.utc).isoformat()

    cur.execute(
         "INSERT INTO deliveries(run_id, drop_idx, start_ts) VALUES (?,?,?)",
         (run_id, drop_idx, start_ts),
        )
    conn.commit()
    return redirect(url_for("index", _anchor=f"drop-{drop_idx}"))

def stop_delivery_logic(run_id, drop_idx):
    conn = get_db()
    cur = conn.cursor()

    end_ts = datetime.now(timezone.utc).isoformat()

    row = cur.execute(
        """
        SELECT start_ts
        FROM deliveries
        WHERE run_id = ? AND drop_idx = ?
        """,
        (run_id, drop_idx),
    ).fetchone()

    start_ts = row["start_ts"]

    # Convert to datetime objects
    end_dt = datetime.fromisoformat(end_ts)
    start_dt = datetime.fromisoformat(start_ts)

    # Convert both to Sydney time
    sydney_end = convert_to_sydney(end_dt)
    sydney_start = convert_to_sydney(start_dt)

    # Calculate elapsed time
    elapsed = sydney_end - sydney_start
    pretty_elapsed = str(elapsed).split(".")[0]

    run = cur.execute(
        "SELECT start_time, end_time, number_of_drops FROM run WHERE id = ?",
        (run_id,)
    ).fetchone()
    
    breaks = cur.execute(
        "SELECT scheduled_time, start_ts FROM breaks WHERE run_id = ?",(run_id,)
    ).fetchall()

    start = run["start_time"]
    end = run["end_time"]

    drops = run["number_of_drops"]

    run_start_dt = datetime.fromisoformat(start)
    run_end_dt = datetime.fromisoformat(end)

    total_break_minutes = 0 

    for i,b in enumerate(breaks):
        if b["start_ts"]:
            if i == 0:
                total_break_minutes += 15
            elif i == 1:
                total_break_minutes += 30 

    shift_minutes = (run_end_dt - run_start_dt).total_seconds() / 60
    work_minutes = shift_minutes - total_break_minutes
    expected_minutes = work_minutes / drops
    elapsed_minutes = elapsed.total_seconds() / 60

    if elapsed_minutes < expected_minutes:
        status = "early"
    elif elapsed_minutes == expected_minutes:
        status = "on_time"
    else:
        status = "late"

    cur.execute(
        """
        UPDATE deliveries
        SET end_ts = ?, elapsed = ?, expected_minutes = ?, status = ? WHERE run_id = ? AND drop_idx = ?
        """,
        (end_ts, pretty_elapsed, expected_minutes, status, run_id, drop_idx)
    )

    conn.commit()

    return redirect(url_for("index", _anchor=f"drop-{drop_idx}"))

