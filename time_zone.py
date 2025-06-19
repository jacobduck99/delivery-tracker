from datetime import date, datetime, timezone  

def convert_timedate(start):
    today = date.today() 
    time = start
    parsed_time = datetime.strptime(start, "%H:%M").time() 
    date_time = datetime.combine(today, parsed_time)
    utc_date_time = date_time.replace(tzinfo=timezone.utc)
    return utc_date_time

def convert_to_sydney(utc_dt):
    return utc_dt.astimezone(SYDNEY)

