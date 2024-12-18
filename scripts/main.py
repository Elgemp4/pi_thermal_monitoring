#!/usr/bin/env python3

from pyvirtualcam import PixelFormat
from camera_controller import CameraController
from firebase_socket import SocketManager
from video_stream import start_stream, stop_stream, is_streaming
from image_processor import ImageProcessor
from temperature import Zone

import pyvirtualcam
import time
import signal
import sys

next_time_to_send = time.time()

time_for_next_alert = 0
over_limit = 0

all_camera = Zone("all", "all", 0, 192, 0, 256)


def cleanly_close_program(sig, frame):
	print("\nExiting gracefully...")
	#cap.release() TODO
	if(is_streaming()):
		stop_stream()
	sys.exit()

signal.signal(signal.SIGINT, cleanly_close_program)
signal.signal(signal.SIGTERM, cleanly_close_program)
	

def handle_stream_state(stream_until : time) -> None:
	if(stream_until > time.time() and not is_streaming()):
		start_stream(sm.stream_url)
	elif(stream_until < time.time() and is_streaming()):
		stop_stream()

def send_temperature_data(sm : SocketManager, th_data : list) -> None:
	global next_time_to_send

	if(sm.measure_each != -1 and next_time_to_send < time.time()):
		data = {}
		print("Sending temperature data")
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

try:
	camera_controller = CameraController()
	camera_controller.connect_camera()

	with pyvirtualcam.Camera(camera_controller.get_width(), camera_controller.get_height(), 25, fmt=PixelFormat.BGR) as virtual_camera:
		print(f'Virtual cam started: {virtual_camera.device} ({virtual_camera.width}x{virtual_camera.height} @ {virtual_camera.fps}fps)')
		with SocketManager() as sm:
			while True:
				if(sm.listen_firebase() == False): #If the connection is closed,
					print("Connection closed")
					break #TODO: Reconnect

				try:
					heatmap_image, th_data = camera_controller.get_frame_data()

					handle_stream_state(sm.stream_until)

					handle_alerts(sm, th_data)
					
					send_temperature_data(sm, th_data)

					virtual_camera.send(heatmap_image)
				except Exception as e:
					print(e)
					pass # Do nothing, just skip this frame
finally:
	cleanly_close_program(None, None)