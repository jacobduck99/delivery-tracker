from flask import Flask, render_template, request, redirect, url_for, session
from timer_utils import record_start, stop_timer, track_time, drop_to_drop_time, humanize_history


app = Flask(__name__)
app.secret_key = "a-very-secret-value"


@app.route("/configuration", methods=["GET", "POST"])
def configuration():
    if request.method == "POST":
        van_number = request.form.get('van_number')
        shift_start = request.form.get('shift_start')
        shift_end = request.form.get('shift_end')
        number_of_drops = request.form.get('num_drops')

        num_drops_int = int(number_of_drops)
        
        session['van_number']  = van_number
        session['shift_start'] = shift_start
        session['shift_end']   = shift_end
        session['num_drops']   = num_drops_int

        return redirect(url_for('index'))
    return render_template("configuration.html")          


@app.route("/", methods=["GET", "POST"])
def index():
    raw       = session.get("history", [])
    history   = humanize_history(raw)
    
    # build and format the drive-time gaps
    drop_to_drop_times = []
    for i in range(1, len(raw)):
        prev = raw[i-1]
        curr = raw[i]
        gap  = drop_to_drop_time(prev, {'start_time': curr['start_time']})
    # *** replace strftime with manual formatting ***
        total_secs = int(gap.total_seconds())
        h = total_secs // 3600
        m = (total_secs % 3600) // 60
        s = total_secs % 60
        drop_to_drop_times.append(f"{h:02}:{m:02}:{s:02}")

    
    return render_template(
      "index.html",
      history=history,
      elapsed=session.get("elapsed"),
      travel_time=session.get("travel_time"),
      drop_to_drop_times=drop_to_drop_times, num_drops = session.get("num_drops", 0)
    )


@app.route("/deliveries", methods=["POST"])
def start_delivery():
    action = request.form.get('action')
    if action == 'start':
        history = session.get('history', [])
        record_start(session)
        if history and 'end_time' in history[-1]:
            previous = history[-1]
            current = {'start_time': session['start_time']}
            gap = drop_to_drop_time(previous, current)
            session['travel_time'] = str(gap)
        return redirect(url_for('index'))

    elif action == 'stop':
        stop_timer(session)
        elapsed = track_time(session)
        session['elapsed'] = elapsed
        history = session.get('history', [])
        history.append({
            'start_time': session['start_time'],
            'end_time': session['end_time'],
            'elapsed': session['elapsed'],
        })
        session['history'] = history 

        session.pop('start_time', None)
        session.pop('end_time',   None)
        session.pop('elapsed',    None)

        
        return redirect(url_for('index'))
    

@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("configuration"))

    

    


        

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)