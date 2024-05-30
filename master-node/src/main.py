import os
import threading
import signal
import time
import json
import subprocess
from flask import Flask, render_template
import paho.mqtt.client as mqtt
import paho.mqtt.client as mqtt

# MQTT Broker details
NETWORK_INTERFACE = os.environ.get("NETWORK_INTERFACE")
BROKER_ADDRESS = os.environ.get("BROKER_ADDRESS")
TOPIC = "main"
KEEPALIVE = 10

app = Flask(__name__)
data = {}
network_topology = {}
network_info = {}

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
            add_network_info(id, payload["network_info"])
            msg["operationState"] = "COMPLETED"
        else:
            msg["operationState"] = "FAILED"
        client.publish(TOPIC, json.dumps(msg))
        print("Published data {}".format(msg))
    elif operation == "data_transfer":
        if id in data.keys():
            print("Received data {} from table {}".format(payload["data"], id))
            data[id].update(payload["data"])
            data[id]["alive"] = True

@app.route('/get_data', methods=['GET'])
def get_data():
    global data
    return json.dumps(data)

@app.route('/network_topology', methods=['GET'])
def get_network_topology():
    global network_topology
    return json.dumps(network_topology)

@app.route('/network_info', methods=['GET'])
def get_network_info():
    global network_info
    return json.dumps(network_info)

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

def add_network_info(id, new_info = None):
    global network_info
    
    # get master mac address
    master_mac = None
    if 0 not in network_info.keys():
        master_mac = new_info['mac_addr']
    else:
        master_mac = network_info[0]['mac_addr']
    
    print(master_mac)
    print(new_info)
    if new_info:
        if id != 0:
            # get only the useful info
            useful_info = {}
            for key in new_info.keys():
                print(key)
                if key == master_mac:
                    useful_info[0] = new_info[key]
                    useful_info['mac_addr'] = new_info['mac_addr']
                    break
        else:
            useful_info = new_info

        # checking if this is a node that is reconnecting before it has been deleted from data_ids
        idToDelete = None
        for nodeId, nodeInfo in network_info.items():
            if useful_info['mac_addr'] == nodeInfo['mac_addr']:
                print("Deleting id {} from data IDs {}".format(nodeId, data.keys()))
                idToDelete = nodeId
                break
        if idToDelete:
            del data[idToDelete]
            remove_network_info(idToDelete)

        network_info[id] = useful_info
        print("Inserted info:")
        print(id)
        print(useful_info)
        print(useful_info['mac_addr'])

        print("SWAPPING OUT MACS")
        # swap out mac addresses for ids
        for nodeId, nodeInfo in network_info.items():
            print(nodeId)
            print(nodeInfo)
            temp_info = {}
            for key, content in nodeInfo.items():
                if key != 'mac_addr':
                    for node_id, node_info in network_info.items():
                        if key == node_info['mac_addr']:
                            key = node_id
                        if content['Nexthop'] == node_info['mac_addr']:
                            content['Nexthop'] = node_id

                temp_info[key] = content
                print(temp_info)
                    
            network_info[nodeId] = temp_info

        # update network topology
        update_network_topology()

def remove_network_info(id):
    if id in network_info.keys():
        node_mac = network_info[id]['mac_addr']
        updated_master_info = {}
        for key, node_info in network_info[0].items():
            if key != 'mac_addr':
                if key == id:
                    key = node_mac
                if node_info['Nexthop'] == id:
                    node_info['Nexthop'] = node_mac
                updated_master_info[key] = node_info

        updated_master_info['mac_addr'] = network_info[0]['mac_addr']
        network_info[0] = updated_master_info       
        del network_info[id]
        
        # update network topology
        update_network_topology()

def update_network_topology():
    global network_info
    global network_topology

    network_topology = {}
    masterInfo = network_info[0]
    node_ids = list(network_info.keys())
    node_ids.remove(0)

    print(node_ids)
    # first find all 1 hop nodes
    for id, node_info in masterInfo.items():
        if id != 'mac_addr':
            if id == node_info['Nexthop']:
                if 1 not in network_topology.keys():
                    network_topology[1] = []
                network_topology[1].append(id)
                if id in node_ids:
                    node_ids.remove(id)

    print(network_topology)
    print(node_ids)
    i = 2
    while len(node_ids) > 0:
        for id in node_ids:
            node_info = network_info[id]
            if node_info[0]['Nexthop'] in network_topology[i-1]:
                if i not in network_topology:
                    network_topology[i] = []
                network_topology[i].append(id)
                if id in node_ids:
                    node_ids.remove(id)
        i += 1
        print(network_topology)
        print(node_ids)

    # clean up in case any nodes were added that arent in the table tracker
    for node_ids in network_topology.values():
        for node_id in node_ids:
            if node_id not in list(network_info.keys()):
                node_ids.remove(node_id)

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

def start_data():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect(BROKER_ADDRESS, 1883, 60)
    client.subscribe(TOPIC)
    client.loop_start()

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
    add_network_info(0, network_info)

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
            remove_network_info(id)

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
