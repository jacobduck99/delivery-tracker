from flask import Flask, render_template, request, redirect, url_for, session
from timer_utils import record_start, stop_timer, track_time, drop_to_drop_time


app = Flask(__name__)
app.secret_key = "a-very-secret-value"


@app.route("/", methods=["GET"])
def index():
    history = session.get("history", [])
    # build a list of timedeltas (as strings) between each pair
    drop_to_drop_times = []
    from timer_utils import drop_to_drop_time
    for i in range(1, len(history)):
        prev = history[i-1]
        curr = history[i]
        # curr only has start & end & elapsed, so we need a dict with start_time
        gap = drop_to_drop_time(prev, {'start_time': curr['start_time']})
        drop_to_drop_times.append(str(gap))
    return render_template(
        "index.html",
        history=history,
        elapsed=session.get("elapsed"),
        travel_time=session.get("travel_time"),
        drop_to_drop_times=drop_to_drop_times
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

    

    


        

if __name__ == "__main__":
    app.run(debug=True)
