import socket
from dotenv import load_dotenv
import os
import json
import subprocess

from zone import Zone

class SocketManager:
    zone_list: list[Zone] = []
    stream_url = ''
    stream_until = 0
    measure_each = -1
    max_temp = -1
    firebase_script = None

    def __enter__(self):
        load_dotenv()
        self.start_firebase()
        self.open_socket()
        return self

    def start_firebase(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        firestore_path = os.path.join(script_dir, 'firestore.js')
        self.firebase_script = subprocess.Popen([os.getenv("NODE_PATH"), firestore_path], stdout=subprocess.PIPE)

    def open_socket(self):
        HOST = os.getenv('HOST')
        PORT = int(os.getenv('PORT'))

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((HOST, PORT))
        self.socket.listen()

        print(f"Listening on {HOST}:{PORT}...")
        self.conn, self.addr = self.socket.accept()
        self.conn.setblocking(False)
        print(f"Connection accepted from {self.addr}")

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        self.socket.close()
        self.firebase_script.kill()

    def listen_firebase(self):
        data = None
        try:
            data = self.conn.recv(1024)
            if not data:
                print("Firebase disconnected, restarting...")
                self.start_firebase()
                self.open_socket()
            
            messages = data.decode().split('\n')

            for message in messages:
                try:
                    jsonMessage = json.loads(message)
                    match jsonMessage['type']:
                        case 'zones':
                            self._on_zone_received(jsonMessage['data'])
                        case 'settings':
                            self._on_settings_received(jsonMessage['data'])
                except json.JSONDecodeError:
                    pass                    
        except BlockingIOError:
            pass

    def _on_zone_received(self, zones: dict):
        self.zone_list.clear()
        for key, value in zones.items():
            self.zone_list.append(Zone(key,value["name"], value["endY"], value["startY"], value["startX"], value["endX"]))


    def _on_settings_received(self, settings):
        self.max_temp = settings['max_temp']['value']
        self.measure_each = settings['measure_each']['value']
        self.stream_url = settings['incoming_url']['value']
        self.stream_until = settings['stream_until']['value']["seconds"]

    def send_temperature_data(self, data):
        self.conn.sendall(json.dumps({"type": "temperatures", "data": data}).encode())

    def send_alert(self):
        self.conn.sendall(json.dumps({"type": "alert"}).encode())