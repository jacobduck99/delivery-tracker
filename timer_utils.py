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

def drop_to_drop_time(previous_drop: dict, current_drop: dict):
    # turn the stored ISO strings back into datetimes
    prev_end   = datetime.fromisoformat(previous_drop['end_time'])
    curr_start = datetime.fromisoformat(current_drop['start_time'])

    # return the interval between them
    return curr_start - prev_end


def humanize_history(raw_history):
    nice = []
    for rec in raw_history:
        start_dt = datetime.fromisoformat(rec['start_time'])
        end_dt = datetime.fromisoformat(rec['end_time'])
        nice.append({'start': start_dt.strftime("%I:%M:%S %p"),  
            'end':   end_dt.strftime("%I:%M:%S %p"),
            'elapsed': rec['elapsed'],})
    return nice