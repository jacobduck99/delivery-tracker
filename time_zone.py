from datetime import date, datetime, timezone  
from zoneinfo import ZoneInfo

SYDNEY = ZoneInfo("Australia/Sydney")

def convert_timedate(time_str):
    now_sydney = datetime.now(SYDNEY)
    parsed_time = datetime.strptime(time_str, "%H:%M").time()
    
    local_dt = datetime.combine(now_sydney.date(), parsed_time).replace(tzinfo=SYDNEY)   

    return local_dt.astimezone(ZoneInfo("UTC"))

def convert_to_sydney(utc_dt):
    return utc_dt.astimezone(SYDNEY)

