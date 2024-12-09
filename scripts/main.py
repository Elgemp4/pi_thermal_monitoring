#!/usr/bin/env python3

from pyvirtualcam import PixelFormat
from linuxpy.video.device import Device, BufferType
from dotenv import load_dotenv


import cv2
import pyvirtualcam
import numpy as np
import argparse
import io
import socket
import json
import os
import time

class Zone:
	def __init__(self, id, name, bottom, top, left, right):
		self.name = name
		self.id = id
		self.bottom = min(bottom, top)
		self.top = max(bottom, top)
		self.left = min(left, right)
		self.right = max(left, right)

	def set_th_data(self, th_data):
		self.th_data = th_data[self.bottom:self.top, self.left:self.right]

	def find_highest(self):
		linear_max = self.th_data[...].argmax()
		row, col = np.unravel_index(linear_max, self.th_data.shape)
		return (col, row, self.th_data[row, col])

	def find_lowest(self):
		linear_max = self.th_data[...].argmin()
		row, col = np.unravel_index(linear_max, self.th_data.shape)
		return (col, row, self.th_data[row, col])

	def find_average(self):
		return round(self.th_data[...].mean(), 2)


#We need to know if we are running on the Pi, because openCV behaves a little oddly on all the builds!
#https://raspberrypi.stackexchange.com/questions/5100/detect-that-a-python-program-is-running-on-the-pi
def is_raspberrypi():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower(): return True
    except Exception: pass
    return False

def find_camera_device():
	for dev_i in range(64):
		try:
			with Device.from_id(dev_i) as device:
				device.open()
				if("USB Camera" in device.info.card and len(device.info.inputs) > 0 and device.info.buffers[0] == BufferType.VIDEO_CAPTURE):
					print(f"Found thermal camera at /dev/video{dev_i}")
					print(f"Device id: {device.info.card}")
					print(f"Device buff: {device.info.buffers}")
					print(f"Device inputs: {device.info.inputs}")
					print("--------------------------------")
					return dev_i
		except FileNotFoundError:
			pass

	raise Exception("No camera device found")

load_dotenv()
HOST = os.getenv('HOST')
PORT = int(os.getenv('PORT'))

isPi = is_raspberrypi()

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=int, default=0, help="Video Device number e.g. 0, use v4l2-ctl --list-devices")
args = parser.parse_args()
	
if args.device:
	dev = args.device
else:
	try:
		dev = find_camera_device()
	except Exception as e:
		dev = 0

zone_list: list[Zone] = []
stream_url = ''
measure_each = -1
max_temp = -1


width = 256 
height = 192 

cap = cv2.VideoCapture('/dev/video'+str(dev), cv2.CAP_V4L)
cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)
print('/dev/video'+str(dev))

scale = 1 #scale multiplier
scaled_width = width * scale
scaled_height = height * scale
alpha = 1.0 # Contrast control (1.0-3.0)
colormap_index = 0
font=cv2.FONT_HERSHEY_SIMPLEX
dispFullscreen = False
rad = 0 #blur radius
threshold = 2
hud = True
recording = False
elapsed = "00:00:00"
snaptime = "None"



colormaps = [('Jet', cv2.COLORMAP_JET),
			 ('Hot', cv2.COLORMAP_HOT),
			 ('Magma', cv2.COLORMAP_MAGMA),
			 ('Inferno', cv2.COLORMAP_INFERNO),
			 ('Plasma', cv2.COLORMAP_PLASMA),
			 ('Bone', cv2.COLORMAP_BONE),
			 ('Spring', cv2.COLORMAP_SPRING),
			 ('Autumn', cv2.COLORMAP_AUTUMN),
			 ('Viridis', cv2.COLORMAP_VIRIDIS),
			 ('Parula', cv2.COLORMAP_PARULA)]


def apply_color_map(colormap_index):
	colormap_title, colormap = colormaps[colormap_index]
	heatmap = cv2.applyColorMap(bgr, colormap)
	return colormap_title, heatmap





# Converting the raw values to celsius
# https://www.eevblog.com/forum/thermal-imaging/infiray-and-their-p2-pro-discussion/200/
# Huge props to LeoDJ for figuring out how the data is stored and how to compute temp from it.
# Basically the temperatures are stored on 14 bits in kelvin multiplied by 16
# As the data is stored on two different bytes they need to be recombined in a single 16 bits unsigned integer
# So the formula is (raw_temp >> 2) / 16 to get the temperature in Kelvin
# Then we substract 273.15 to convert Lelvin in Celcius
# Simplified the equation become : raw_temp / 64 - 273.15
# The data is then rounded for ease of use
def convertRawToCelcius(raw_temp):
	return np.round(((raw_th_data[..., 1].astype(np.uint16) << 8) + raw_th_data[..., 0].astype(np.uint16)) / 64 - 273.15, 2)


def listenForIncommingData():
	data = None
	try:
		data = conn.recv(1024)
		if not data:
			return False
		
		messages = data.decode().split('\n')

		for message in messages:
			try:
				jsonMessage = json.loads(message)
				match jsonMessage['type']:
					case 'zones':
						onZoneReceived(jsonMessage['data'])
					case 'settings':
						onSettingsReceived(jsonMessage['data'])
			except json.JSONDecodeError:
				print("Error decoding json : " + message)
				pass

		
	except BlockingIOError:
		pass

	return True

def onZoneReceived(zones: dict):
	global zone_list
	zone_list.clear()
	for key, value in zones.items():
		zone_list.append(Zone(key,value["name"], value["endY"], value["startY"], value["startX"], value["endX"]))


def onSettingsReceived(settings):
	global max_temp, measure_each, stream_url
	max_temp = settings['max_temp']['value']
	measure_each = settings['measure_each']['value']
	stream_url = settings['stream_url']['value']

def send_temperature_data(data):
	conn.sendall(json.dumps({"type": "temperatures", "data": data}).encode())




with pyvirtualcam.Camera(width, height, 25, fmt=PixelFormat.BGR, print_fps=25) as cam:
	print(f'Virtual cam started: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)')

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.bind((HOST, PORT))
		s.listen()
		conn, addr = s.accept()
		conn.setblocking(False)

		next_time_to_send = 0
		while cap.isOpened():
			if(listenForIncommingData() == False): #If the connection is closed,
				break

			# Capture frame-by-frame
			ret, frame = cap.read()
			if ret:
				im_data,raw_th_data = np.array_split(frame, 2)
				th_data = convertRawToCelcius(raw_th_data)

				temp = th_data[96, 128]
				# Convert the real image to RGB
				bgr = cv2.cvtColor(im_data, cv2.COLOR_YUV2BGR_YUYV)
				#Contrast
				bgr = cv2.convertScaleAbs(bgr, alpha=alpha)#Contrast

				#bicubic interpolate, upscale and blur
				bgr = cv2.resize(bgr, (scaled_width, scaled_height), interpolation=cv2.INTER_CUBIC)#Scale up!
				if rad>0:
					bgr = cv2.blur(bgr,(rad,rad))


				#apply colormap
				cmapText, image = apply_color_map(colormap_index)

				if(measure_each != -1 and next_time_to_send < time.time()):
					data = {}
					print("Zones : " + str(zone_list))
					print("Max temp : " + str(max_temp))
					for zone in zone_list:
						zone.set_th_data(th_data)
						(x,y,temp) = zone.find_highest()
						data[zone.id] = temp
					print(data)

					next_time_to_send = time.time() + measure_each
					send_temperature_data(data)

				cam.send(image)

	cap.release()