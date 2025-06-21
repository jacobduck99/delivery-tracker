from time_zone import convert_timedate
from datetime import datetime, timezone, date
from flask import request 

def get_iso_timestamp(field_name):
    value = request.form.get(field_name)
    if not value:
        return None
    utc = convert_timedate(value)
    return utc.isoformat()

    
