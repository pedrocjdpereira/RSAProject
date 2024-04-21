import os
import random
import threading
import signal
import time
from flask import Flask, render_template

app = Flask(__name__)
data = 2

@app.route('/', methods=['GET'])
def root():
    return 'Hello World!'
    #return render_template('index.html', data=data)

@app.route('/get_data', methods=['GET'])
def get_data():
    global data
    return str(data)

def start_server():
    app.run(host='0.0.0.0')

def start_data():
    global data
    while True:
        data = random.randint(1,10)
        print(data)
        time.sleep(2)

def signal_handler(signal, frame):
    # Handle Ctrl+C
    print("Ctrl+C detected. Exiting...")
    os._exit(0)  # Terminate the program forcefully

if __name__ == '__main__':
    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Create threads for server and socket
    server_thread = threading.Thread(target=start_server)
    data_thread = threading.Thread(target=start_data)

    # Start the threads
    server_thread.start()
    data_thread.start()

    # Wait for the threads to complete
    server_thread.join()
    data_thread.join()
