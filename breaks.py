from datetime import datetime, timezone
from flask import session 
from time_zone import convert_timedate
from zoneinfo import ZoneInfo

SYDNEY = ZoneInfo("Australia/Sydney")

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

    scheduled_local = scheduled_time.astimezone(SYDNEY)
    print("Scheduled (Sydney):", scheduled_local)
    actual_local = actual_time.astimezone(SYDNEY)
    print("Actual (Sydney):", actual_local)

    delta_minutes = int((actual_local - scheduled_local).total_seconds() / 60)
    
    if delta_minutes > 0:
        status = "late"
    elif delta_minutes < 0:
        status = "early"
        print(f"status (status), {status}")
    else:
        status = "on_time"  

    cur.execute(
        """
        UPDATE breaks
        SET actual_time = ?, late_minutes = ?, status = ?
        WHERE run_id = ? AND break_number = ?
        """,
        (start_ts, delta_minutes, status, run_id, break_number)
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

