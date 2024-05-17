import os
import random
import threading
import signal
import time
import json
import paho.mqtt.client as mqtt

from detect_people import PeopleDetector

# MQTT Broker details
BROKER_ADDRESS = "10.1.1.4"
TOPIC = "main"
RECONNECT_DELAY = 5
MAX_RECONNECT_COUNT = 10

id = -1
id_accepted = False

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def on_disconnect(client, userdata, rc):
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
    global id_accepted

    # Decode the payload and extract the ID
    try:
        payload = json.loads(msg.payload)
        msg_id = payload["id"]
        operation = payload["operation"]
        operationState = payload["operationState"]
    except Exception as e:
        print("ERROR: {}".format(e))

    if msg_id == id:
        if operation == "reserve_id":
            if operationState == "COMPLETED":
                print("ID {} is accepted.".format(msg_id))
                id_accepted = True
            elif operationState == "FAILED":
                print("ID {} is invalid. Generating a new ID.".format(msg_id))
                generate_id(client)

def generate_id(client):
    global id

    id = random.randint(1,10)
    msg = {
        "id": id,
        "operation": "reserve_id",
        "operationState": "PROCESSING",
    }
    client.publish(TOPIC, json.dumps(msg))
    print("Published data {} to topic {}".format(msg, TOPIC))
    time.sleep(2)

def start_data():
    # Create MQTT client
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    while True:
        try:
            client.connect(BROKER_ADDRESS, 1883, 60)
            break
        except Exception as e:
            time.sleep(RECONNECT_DELAY)
            print("ERROR:{}".format(e))
    client.subscribe(TOPIC)
    client.loop_start()
    
    while not id_accepted:
        generate_id(client)
        time.sleep(2)

    global peopleDetector
    while True:
        data = {}
        msg = {
            "id": id,
            "operation": "data_transfer",
            "operationState": "COMPLETED",
            "data": peopleDetector.getData()
        }
        client.publish(TOPIC, json.dumps(msg))
        print("Published msg {}. id = {}".format(msg["data"], id))
        time.sleep(1)

def signal_handler(signal, frame):
    # Handle Ctrl+C
    print("Ctrl+C detected. Exiting...")
    os._exit(0)  # Terminate the program forcefully

if __name__ == '__main__':
    peopleDetector = PeopleDetector("peopleSitting_example1.mp4", 200)

    # Create thread for data
    data_thread = threading.Thread(target=start_data)
    getSeats_thread = threading.Thread(target=peopleDetector.getSeats)

    # Start the thread
    data_thread.start()
    getSeats_thread.start()

    # Wait for the thread to complete
    data_thread.join()
    getSeats_thread.join()