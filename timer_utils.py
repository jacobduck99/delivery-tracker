from datetime import datetime

def record_start(record):
    start = datetime.now().isoformat()
    record['start_time'] = start


def stop_timer(record):
    end = datetime.now().isoformat()
    record['end_time'] = end


def track_time(record):
    # parse your stored ISO strings back into datetimes
    start_dt = datetime.fromisoformat(record['start_time'])
    end_dt   = datetime.fromisoformat(record['end_time'])
    
    # compute the timedelta
    elapsed_delta = end_dt - start_dt
    
    # convert to total seconds (int), then break out H, M, S
    total_secs = int(elapsed_delta.total_seconds())
    hours   = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    seconds = total_secs % 60
    
    # format as HH:MM:SS
    pretty = f"{hours:02}:{minutes:02}:{seconds:02}"
    return pretty
 


