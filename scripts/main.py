#!/usr/bin/env python3

from pyvirtualcam import PixelFormat
from temperature import convertRawToCelcius
from system_utils import find_camera_device
from firebase_socket import SocketManager
from video_stream import start_stream, stop_stream, is_streaming

from temperature import Zone

import cv2
import pyvirtualcam
import numpy as np
import time
import signal
import sys
import os


dev = find_camera_device()
camera_path = '/dev/video'+str(dev)

camera_width = 256 
camera_height = 192 

cap = cv2.VideoCapture(camera_path, cv2.CAP_V4L)
cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)
print(camera_path)

next_time_to_send = time.time()

time_for_next_alert = 0
over_limit = 0
all_camera = Zone("all", "all", 0, 192, 0, 256)

scale = 1 #scale multiplier
scaled_width = camera_width * scale
scaled_height = camera_height * scale
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


def cleanly_close_program(sig, frame):
	print("\nExiting gracefully...")
	cap.release()
	if(is_streaming()):
		stop_stream()
	sys.exit()

signal.signal(signal.SIGINT, cleanly_close_program)
signal.signal(signal.SIGTERM, cleanly_close_program)


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


def apply_color_map(colormap_index, im_data):
	bgr = cv2.cvtColor(im_data, cv2.COLOR_YUV2BGR_YUYV)
	bgr = cv2.convertScaleAbs(bgr, alpha=alpha)#Contrast

	bgr = cv2.resize(bgr, (scaled_width, scaled_height), interpolation=cv2.INTER_CUBIC)#Scale up!
	if rad>0:
		bgr = cv2.blur(bgr,(rad,rad))

	colormap_title, colormap = colormaps[colormap_index]
	heatmap_image = cv2.applyColorMap(bgr, colormap)
	return heatmap_image
	

def handle_camera_reconnect():
	global cap
	global camera_path
	global dev

	if(os.path.exists(camera_path) == False or cap.isOpened() == False):
		print("Camera disconnected, attempting to reconnect in 5 seconds")
		cap.release()
		time.sleep(5)
		
		dev = find_camera_device()
		camera_path = '/dev/video'+str(dev)

		cap.open(camera_path, cv2.CAP_V4L)
		cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)

def handle_stream_state(stream_until : time) -> None:
	if(stream_until > time.time() and not is_streaming()):
		start_stream(sm.stream_url)
	elif(stream_until < time.time() and is_streaming()):
		stop_stream()

def send_temperature_data(sm : SocketManager, th_data : list) -> None:
	global next_time_to_send

	if(sm.measure_each != -1 and next_time_to_send < time.time()):
		data = {}

		for zone in sm.zone_list:
			zone.set_th_data(th_data)
			(x,y,temp) = zone.find_highest()
			data[zone.id] = temp
	
		next_time_to_send = time.time() + sm.measure_each
		sm.send_temperature_data(data)

def handle_alerts(sm : SocketManager, th_data : list) -> None:
	global over_limit
	global time_for_next_alert
	global all_camera

	all_camera.set_th_data(th_data)

	(x,y,temp) = all_camera.find_highest()

	if(temp >= sm.max_temp):
		over_limit += 1
	else:
		over_limit = -1

	if(over_limit >= 100):
		if(time_for_next_alert > time.time()):
			sm.send_alert()
			time_for_next_alert = time.time() + 10
	
def parse_frame(frame):
	im_data,raw_th_data = np.array_split(frame, 2)
	th_data = convertRawToCelcius(raw_th_data)
	heatmap_image = apply_color_map(colormap_index, im_data)
	return heatmap_image, th_data

try:
	with pyvirtualcam.Camera(camera_width, camera_height, 25, fmt=PixelFormat.BGR, print_fps=25) as cam:
		print(f'Virtual cam started: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)')
		with SocketManager() as sm:
			while True:
				if(sm.listen_firebase() == False): #If the connection is closed,
					print("Connection closed")
					break #TODO: Reconnect

				frame_acquired, frame = cap.read()

				if not frame_acquired:
					handle_camera_reconnect()
					continue

				try:
					heatmap_image, th_data = parse_frame(frame)

					handle_stream_state(sm.stream_until)

					handle_alerts(sm, th_data)
					
					send_temperature_data(sm, th_data)

					cam.send(heatmap_image)
				except Exception as e:
					print(e)
finally:
	cleanly_close_program(None, None)