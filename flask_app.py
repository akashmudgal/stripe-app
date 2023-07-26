from flask import Flask, render_template, request,flash
from multiprocessing import Process
import time
import random
from script import make_payment
app = Flask(__name__)
app.secret_key = "super secret key"

running=False
script_process=None

def execute_script(start_time, amount_range,fixed_time_interval=None, random_intervals_range=None):
    while True:
        current_time = time.time()
        #start_time_unix = start_time.timestamp()
        time_diff = current_time - start_time

        if time_diff >= 0:
            amount=random.randint(amount_range[0],amount_range[1])
            #ensure amount is in multiples of 50
            amount=amount - amount % 50
            # Execute your script here
            print("Executing the script at:", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time)))
            make_payment(str(amount))

            if random_intervals_range:
                # Randomize the time interval between 5 and 30 seconds
                time_interval = random.randint(random_intervals_range[0],random_intervals_range[1])
            else:
                time_interval = fixed_time_interval

            time.sleep(time_interval*60)

@app.route("/", methods=["GET", "POST"])
def index():
    global running
    global script_process
    if request.method == "POST":
        start_time = request.form.get("start_time")
        is_time_random = request.form.get("time_intervals_random") == "on"

        fixed_interval=None
        random_intervals_range=None

        #if script execution is set for random time intervals, read the random time intervals range from form
        if is_time_random:
            range_start=int(request.form.get("time_range_start",1))
            range_end=int(request.form.get("time_range_end",1))
            random_intervals_range=[range_start,range_end]
        else:
            #read the fixed interval value
            fixed_interval = int(request.form.get("time_interval", 10))

        #get the amount range from the form
        amount_range_start=int(request.form.get("amount_range_start", 50))
        amount_range_end=int(request.form.get("amount_range_end", 1000))
        amount_range = [amount_range_start,amount_range_end]

        start_time = time.strptime(start_time, "%Y-%m-%dT%H:%M")
        start_time = time.mktime(start_time)

        if not running:
            # Create a separate thread to execute the script
            script_process=Process(target=execute_script,args=(start_time, amount_range, fixed_interval, random_intervals_range))
            script_process.start()
            flash("Script Execution scheduled as per the parameters!!")
            running=True


    return render_template("form.html", running=running)

@app.route("/stop", methods=["GET"])
def stop_script():
    global running
    global script_process
    if running:
        running = False
        script_process.kill()
        flash("Script Thread Stopped!!")
    return app.redirect("/")

if __name__ == "__main__":
    app.run(threaded=True,debug=True,host='0.0.0.0')