from flask import Flask, render_template, request, redirect, url_for, session
from timer_utils import record_start, stop_timer, track_time


app = Flask(__name__)
app.secret_key = "a-very-secret-value"


@app.route("/", methods=["GET"])
def index():
    elapsed = session.get("elapsed")
    history = session.get("history", [])
    return render_template("index.html", elapsed=elapsed, history=history)


@app.route("/deliveries", methods=["POST"])
def start_delivery():
    action = request.form.get('action')
    if action == 'start':
        record_start(session)
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
