from flask import Flask, render_template, request,flash
from multiprocessing import Process,Queue
import time
import random
import subprocess
from datetime import datetime,timedelta
from script import make_payment
import logging
app = Flask(__name__)
app.secret_key = "super secret key"

# Create a queue to communicate script error messages
#error_queue = Queue(maxsize=1)

#logging configuration

#name of the log file
timestamp=datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
filename=f"stripe-app-{timestamp}.log"

#initialize the logging
logging.basicConfig(
    level=logging.DEBUG,
    filename=filename,
    format='[%(asctime)s][%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


#creare the pid file
pid=open('pid','w')
pid.close()

def is_execution_time_valid(execution_time: str) -> bool:
    #Convert execution time from UNIX time to Datetime Stuct
    execution_time_date=time.localtime(execution_time)

    #Calculate working hour timestamps (UNIX) from execution_time 
    min_start_time=time.mktime(time.strptime(f'{execution_time_date.tm_year}-{execution_time_date.tm_mon}-{execution_time_date.tm_mday}T07:00',r"%Y-%m-%dT%H:%M"))
    max_start_time=time.mktime(time.strptime(f'{execution_time_date.tm_year}-{execution_time_date.tm_mon}-{execution_time_date.tm_mday}T19:00',r"%Y-%m-%dT%H:%M"))

    #
    result=execution_time >= min_start_time and execution_time <=max_start_time

    return result

def execute_script(execution_time, amount_range,fixed_time_interval=None, random_intervals_range=None,run_in_working_hours=False):
    next_execution_time=execution_time

    while True:
        execution_time_date=time.localtime(next_execution_time)
        min_start_time=time.mktime(time.strptime(f'{execution_time_date.tm_year}-{execution_time_date.tm_mon}-{execution_time_date.tm_mday}T07:00',r"%Y-%m-%dT%H:%M"))
        max_start_time=time.mktime(time.strptime(f'{execution_time_date.tm_year}-{execution_time_date.tm_mon}-{execution_time_date.tm_mday}T19:00',r"%Y-%m-%dT%H:%M"))
        current_time = time.time()
        
        #difference between proposed execution time and current time
        time_diff = next_execution_time - current_time
        if time_diff < 0:
            amount=random.randint(amount_range[0],amount_range[1])
            #ensure amount is in multiples of 50
            amount=amount - amount % 50
            # Execute your script here
            logging.info(f"Executing the payment at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
            make_payment(str(amount))

            if random_intervals_range:
                # Randomize the time interval between the given range
                time_interval = random.randint(random_intervals_range[0],random_intervals_range[1]) * 60
            else:
                time_interval = fixed_time_interval * 60

            # get the next execution time
            current_time=time.mktime(time.strptime(datetime.now().strftime("%Y-%m-%dT%H:%M"),"%Y-%m-%dT%H:%M"))
            next_execution_time = current_time + time_interval

            #delay in next payment(seconds)
            delay=time_interval

            if run_in_working_hours and next_execution_time > max_start_time:
                #Get the difference
                time_diff=next_execution_time - max_start_time
                next_execution_time = min_start_time + 86400 + time_diff

                delay = next_execution_time - current_time

            logging.info(f"Next payment will be made in {delay} seconds.")
            
            time.sleep(delay)
            
@app.route("/", methods=["GET", "POST"])
def index():
    with open('pid','r+') as read_stream:
        pid=read_stream.read()
        read_stream.close()
    
    write_stream=None

    if not pid and request.method == "POST":
        try:
            start_time = request.form.get("start_time")
            is_time_random = request.form.get("time_intervals_random") == "on"
            run_in_working_hours=request.form.get("working_hours_toggle") == "on"
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

            if run_in_working_hours:
                if not is_execution_time_valid(start_time):
                    flash("The start time must be in working hours (7:00 AM to 7:00 PM)")
                    return render_template("form.html", running=False)
            # Create a separate thread to execute the script
            script_process=Process(target=execute_script,args=(start_time, amount_range, fixed_interval, random_intervals_range,run_in_working_hours))
            script_process.start()
            #write process pid to file
            write_stream=open('pid','w')
            pid=str(script_process.pid)
            write_stream.write(str(script_process.pid))
        except Exception as e:
            write_stream=open('pid','w')
            flash(f"An error occured while scheduling script. Please try again. {e}")
    
    if write_stream:
        write_stream.close()

    running=bool(pid)

    return render_template("form.html", running=running)

@app.route("/stop", methods=["GET"])
def stop_script():
    subprocess.run(['/bin/bash', '-c', '[ -f pid ] && [ -s pid ] && kill -9 $(/usr/bin/cat pid) && > pid'])
    time.sleep(2)
    flash("Script Thread Stopped!!")
    return app.redirect("/")

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)