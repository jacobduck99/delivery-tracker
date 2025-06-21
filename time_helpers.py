from time_zone import convert_timedate
from datetime import datetime, timezone, date
from flask import request 
from time_zone import convert_to_sydney

def get_iso_timestamp(field_name):
    value = request.form.get(field_name)
    if not value:
        return None
    utc = convert_timedate(value)
    return utc.isoformat()

def attach_local_times(deliveries):
    for d in deliveries:
        if d.get("start_ts"):
            start_utc = datetime.fromisoformat(d["start_ts"])
            d["start_local"] = convert_to_sydney(start_utc)

        if d.get("end_ts"):
            end_utc = datetime.fromisoformat(d["end_ts"])
            d["end_local"] = convert_to_sydney(end_utc)
        return deliveries
    


    
