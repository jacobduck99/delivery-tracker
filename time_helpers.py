from time_zone import convert_timedate
from datetime import datetime, timezone, date
from flask import request 
from time_zone import convert_to_sydney
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Australia/Sydney")

def get_iso_timestamp(field_name):
    value = request.form.get(field_name)
    if not value:
        return None
    utc = convert_timedate(value)
    return utc.isoformat()

def attach_local_times(rows):
    result = []
    for d in rows:
        d = dict(d)
        start_ts = d.get("start_ts")
        end_ts = d.get("end_ts")

        # Handle start_ts safely
        if isinstance(start_ts, str):
            try:
                start_utc = datetime.fromisoformat(start_ts)
                d["start_local"] = start_utc.astimezone(TZ).strftime("%H:%M")
            except ValueError:
                print(f"Invalid start_ts: {start_ts}")
                d["start_local"] = None
        else:
            print(f"Missing or invalid start_ts: {start_ts}")
            d["start_local"] = None

        # Handle end_ts safely
        if isinstance(end_ts, str):
            try:
                end_utc = datetime.fromisoformat(end_ts)
                d["end_local"] = end_utc.astimezone(TZ).strftime("%H:%M")
            except ValueError:
                print(f"Invalid end_ts: {end_ts}")
                d["end_local"] = None
        else:
            print(f"Missing or invalid end_ts: {end_ts}")
            d["end_local"] = None

        result.append(d)
    return result


    


    
