import os
import threading
import signal
import time
import json
from flask import Flask, render_template
import paho.mqtt.client as mqtt
import paho.mqtt.client as mqtt

# MQTT Broker details
BROKER_ADDRESS = "mqtt"
TOPIC = "main"
KEEPALIVE = 10

app = Flask(__name__)
data = {}
network_topology = {}

RECONNECT_DELAY = 5
MAX_RECONNECT_COUNT = 10

def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

def on_disconnect(client, userdata, rc, properties=None, session_expiry_interval=None):
    print("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        print("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            print("Reconnected successfully!")
            return
        except Exception as err:
            print("%s. Reconnect failed. Retrying...", err)

        reconnect_count += 1
    print("Reconnect failed after %s attempts. Exiting...", reconnect_count)

def on_message(client, userdata, msg):
    # Decode the payload and extract the ID
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        id = payload["id"]
        operation = payload["operation"]
        operationState = payload["operationState"]
    except Exception as e:
        print("ERROR: {}".format(e))

    global data
    if operation == "reserve_id" and operationState == "PROCESSING":
        print("Received reserve ID request {}".format(payload))
        msg = {
            "id": id,
            "operation": "reserve_id",
        }
        # Check if ID already exists
        if id not in data.keys():
            data[id] = {}
            data[id]["alive"] = True
            update_network(id, payload["network_info"])
            msg["operationState"] = "COMPLETED"
        else:
            msg["operationState"] = "FAILED"
        client.publish(TOPIC, json.dumps(msg))
        print("Published data {}".format(msg))
    elif operation == "data_transfer":
        print("Received data {} from table {}".format(payload["data"], id))
        data[id].update(payload["data"])
        data[id]["alive"] = True

@app.route('/', methods=['GET'])
def root():
    return 'Hello World!'

@app.route('/get_data', methods=['GET'])
def get_data():
    global data
    return str(data)

@app.route('/network_topology', methods=['GET'])
def get_network_topology():
    global network_topology
    return str(network_topology)

@app.route('/', methods=['GET'])
def welcome():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('library.html')

#add a route that shows the live feed of my camera
@app.route('/live_feed', methods=['GET'])
def live_feed():
    return render_template('live_feed.html')
def start_server():
    app.run(host='0.0.0.0', port=8000)

def update_network(id, network_info=None, remove=False):
    global network_topology
    
    if remove:
        if id in network_topology.keys():
            del network_topology[id]
    else:
        if network_info:
            network_topology[id] = network_info

def start_data():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect(BROKER_ADDRESS, 1883, 60)
    client.subscribe(TOPIC)
    client.loop_start()

    global data
    while True:
        time.sleep(KEEPALIVE)
        print("Checking data IDs")
        idsToDelete = []
        for id in data.keys():
            if not data[id]["alive"]:
                print("Deleting id {} from data IDs {}".format(id, data.keys()))
                idsToDelete.append(id)
            else:
                data[id]["alive"] = False
        for id in idsToDelete:
            del data[id]
            update_network(id, remove=True)

def signal_handler(signal, frame):
    # Handle Ctrl+C
    print("Ctrl+C detected. Exiting...")
    os._exit(0)  # Terminate the program forcefully

if __name__ == '__main__':
    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Create threads for server and data and for checking and removing inactive data threads
    server_thread = threading.Thread(target=start_server)
    data_thread = threading.Thread(target=start_data)

    # Start the threads
    server_thread.start()
    data_thread.start()

    # Wait for the threads to complete
    server_thread.join()
    data_thread.join()
