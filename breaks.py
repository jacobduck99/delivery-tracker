from datetime import datetime, timezone
from flask import session 
from time_zone import convert_timedate

def get_scheduled_break(cur, run_id, break_number):
    row = cur.execute(
        """
        SELECT scheduled_time FROM breaks WHERE run_id = ? AND break_number = ?
        """,
        (run_id, break_number)
    ).fetchone()

    if not row:
        return None

    return row["scheduled_time"]

def handle_start_break(cur, run_id, break_number, scheduled_time_str):
    scheduled_time = datetime.fromisoformat(scheduled_time_str)
    actual_time = datetime.now(timezone.utc)
    start_ts = actual_time.isoformat()

    late_minutes = max(0, int((actual_time - scheduled_time).total_seconds() / 60))
    status = "late" if late_minutes > 0 else "on_time"

    cur.execute(
        """
        INSERT OR REPLACE INTO breaks 
        (run_id, break_number, actual_time, scheduled_time, late_minutes, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (run_id, break_number, start_ts, scheduled_time_str, late_minutes, status)
    )


def handle_skip_break(cur, run_id, break_number):
    cur.execute(
        """
        INSERT OR REPLACE INTO breaks
        (run_id, break_number, status)
        VALUES(?,?,?)
        """,
        (run_id, break_number, "skipped")
    )
