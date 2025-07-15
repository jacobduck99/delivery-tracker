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
        start_ts = d.get("start_time")
        end_ts = d.get("end_time")

        # Handle start_ts safely
        if isinstance(start_ts, str):
            try:
                start_utc = datetime.fromisoformat(start_ts)
                d["start_local"] = start_utc.astimezone(TZ).strftime("%H:%M")
            except ValueError:
                d["start_local"] = None
        else:
            d["start_local"] = None

        # Handle end_ts safely
        if isinstance(end_ts, str):
            try:
                end_utc = datetime.fromisoformat(end_ts)
                d["end_local"] = end_utc.astimezone(TZ).strftime("%H:%M")
            except ValueError: 
                d["end_local"] = None
        else:
            d["end_local"] = None

        result.append(d)
    return result


def attach_duration_datetimes(rows):
    for d in rows:
        d["start_dt"] = None
        d["end_dt"] = None
        d["duration_minutes"] = None

        if isinstance(d.get("start_time"), str):
            try:
                d["start_dt"] = datetime.fromisoformat(d["start_time"]).replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)
            except ValueError:
                pass

        if isinstance(d.get("end_time"), str):
            try:
                d["end_dt"] = datetime.fromisoformat(d["end_time"]).replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)
            except ValueError:
                pass

        if d["start_dt"] and d["end_dt"]:
            delta = d["end_dt"] - d["start_dt"]
            d["duration_minutes"] = int(delta.total_seconds() // 60)


    
