import os
import random
import threading
import subprocess
import signal
import time
import json
import paho.mqtt.client as mqtt

from detect_people import PeopleDetector

# MQTT Broker details
BROKER_ADDRESS = os.environ.get("BROKER_IP")
NETWORK_INTERFACE = os.environ.get("NETWORK_INTERFACE")
VIDEO_PATH = os.environ.get("VIDEO_PATH")
SITTING_PARAM = os.environ.get("SITTING_PARAM")
TOPIC = "main"
RECONNECT_DELAY = 5
MAX_RECONNECT_COUNT = 10

id = -1
id_accepted = False
reconnecting = False

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def on_disconnect(client, userdata, rc, properties=None, session_expiry_interval=None):
    print("Disconnected with result code: %s", rc)
    global reconnecting
    global id_accepted
    reconnecting = True
    id_accepted = False
    reconnect_count, reconnect_delay = 0, RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        print("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            print("Reconnected successfully!")
            while not id_accepted:
                generate_id(client)
                time.sleep(2)
            reconnecting = False
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
            elif operationState == "FAILED" and not id_accepted:
                print("ID {} is invalid. Generating a new ID.".format(msg_id))
                generate_id(client)

def parse_network_info(network_info):
    # Initialize dictionary to hold parsed data
    parsed_info = {}

    # Split the output into lines
    lines = network_info.strip().split('\n')

    # Iterate over the relevant lines to extract originator information
    for line in lines[2:]:  # Skip the first two lines (header and column titles)
        if line.strip():  # Skip any empty lines
            parts = line.split()
            
            # Handle lines with an asterisk (*) and without
            if parts[0] == '*':
                originator = parts[1]
                last_seen = parts[2].strip('s')
                nexthop = parts[4]
                
                # Convert last_seen to float, ignore lines that can't be converted
                try:
                    last_seen = float(last_seen)
                except ValueError:
                    continue
                
                # Add the originator information to the parsed_info dictionary
                parsed_info[originator] = {
                    'last-seen': last_seen,
                    'Nexthop': nexthop
                }

    return parsed_info

def generate_id(client):
    global id

    id = random.randint(1,10)

    # Collect Batman information using subprocess
    try:
        network_info = parse_network_info(subprocess.check_output(["sudo", "batctl", "o"]).decode("utf-8"))
    except subprocess.CalledProcessError as e:
        network_info = f"Error collecting batman info: {e}"
        print(network_info)

    # Collect host MAC Address
    try:
        result = subprocess.run(['ifconfig', NETWORK_INTERFACE], stdout=subprocess.PIPE, text=True).stdout
    except subprocess.CalledProcessError as e:
        result = f"Error collecting mac address: {e}"
        print(result)

    for line in result.split('\n'):
        if 'ether' in line:
            network_info["mac_addr"] = line.split()[1]
            break

    msg = {
        "id": id,
        "operation": "reserve_id",
        "operationState": "PROCESSING",
        "network_info": network_info,
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
    global reconnecting
    while True:
        while reconnecting:
            time.sleep(2)
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
    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    peopleDetector = PeopleDetector(VIDEO_PATH, SITTING_PARAM)

    # Create thread for data
    data_thread = threading.Thread(target=start_data)
    if VIDEO_PATH.startswith('rtsp://'):
        discardFrames_thread = threading.Thread(target=peopleDetector.discardFrames)
        getSeats_thread = threading.Thread(target=peopleDetector.getSeats)
    else:
        getSeats_thread = threading.Thread(target=peopleDetector.getSeatsVideo)

    # Start the thread
    data_thread.start()
    if VIDEO_PATH.startswith('rtsp://'):
        discardFrames_thread.start()
    getSeats_thread.start()

    # Wait for the thread to complete
    data_thread.join()
    if VIDEO_PATH.startswith('rtsp://'):
        discardFrames_thread.join()
    getSeats_thread.join()