import socket
from dotenv import load_dotenv
import os
import json
import time
from datetime import datetime, timedelta
import subprocess

from temperature import Zone

class SocketManager:
    zone_list: list[Zone] = []
    stream_url = ''
    stream_until = None
    measure_each = -1
    max_temp = -1
    firebase_script = None

    def __enter__(self):
        load_dotenv()
        HOST = os.getenv('HOST')
        PORT = int(os.getenv('PORT'))

        self.firebase_script = subprocess.Popen([os.getenv("NODE_PATH"), './firestore.js'], stdout=subprocess.PIPE)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen()
        print(f"Listening on {HOST}:{PORT}...")
        self.conn, self.addr = self.socket.accept()
        print(f"Connection accepted from {self.addr}")
        self.conn.setblocking(False)

        

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        self.socket.close()
        self.firebase_script.kill()

    def listen_firebase(self):
        data = None
        try:
            data = self.conn.recv(1024)
            if not data:
                return False
            
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

        return True

    def _on_zone_received(self, zones: dict):
        self.zone_list.clear()
        for key, value in zones.items():
            self.zone_list.append(Zone(key,value["name"], value["endY"], value["startY"], value["startX"], value["endX"]))


    def _on_settings_received(self, settings):
        self.max_temp = settings['max_temp']['value']
        self.measure_each = settings['measure_each']['value']
        self.stream_url = settings['stream_url']['value']
        self.stream_until = settings['stream_until']['value']["seconds"]

        print(self.stream_until)

    def send_temperature_data(self, data):
        self.conn.sendall(json.dumps({"type": "temperatures", "data": data}).encode())