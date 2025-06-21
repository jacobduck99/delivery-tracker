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
        UPDATE breaks
        SET start_ts = ?, late_minutes = ?, status = ?
        WHERE run_id = ? AND break_number = ?
        """,
        (start_ts, late_minutes, status, run_id, break_number)
    )


def handle_skip_break(cur, run_id, break_number):
    cur.execute(
        """
        UPDATE breaks
        SET status = ?
        WHERE run_id = ? AND break_number = ?
        """,
        ("skipped", run_id, break_number)
    )

