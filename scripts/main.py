#!/usr/bin/env python3

from pyvirtualcam import PixelFormat
from camera_controller import CameraController
from firebase_socket import SocketManager
from video_stream_controller import VideoStreamController
from zone import Zone

import pyvirtualcam
import time
import signal
import sys

camera_controller = CameraController()
stream_controller = VideoStreamController()

next_time_to_send = time.time()

time_for_next_alert = 0
over_limit = 0

all_camera = Zone("all", "all", 0, 192, 0, 256)

def cleanly_close_program(sig, frame):
	print("\nExiting gracefully...")
	camera_controller.release()
	stream_controller.stop_stream()
	sys.exit()

signal.signal(signal.SIGINT, cleanly_close_program)
signal.signal(signal.SIGTERM, cleanly_close_program)

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
	print(temp)
	if(temp >= sm.max_temp and over_limit != -1):
		over_limit += 1
	else:
		over_limit = -1

	if(over_limit >= 5):
		if(time_for_next_alert < time.time()):
			sm.send_alert()
			time_for_next_alert = time.time() + 10

try:
	camera_controller.connect_camera()

	with pyvirtualcam.Camera(camera_controller.get_width(), camera_controller.get_height(), 25, fmt=PixelFormat.BGR) as virtual_camera:
		print(f'Virtual cam started: {virtual_camera.device} ({virtual_camera.width}x{virtual_camera.height} @ {virtual_camera.fps}fps)')
		with SocketManager() as sm:
			while True:
				sm.listen_firebase()

				try:
					heatmap_image, th_data = camera_controller.get_frame_data()

					handle_alerts(sm, th_data)
					
					send_temperature_data(sm, th_data)

					virtual_camera.send(heatmap_image)

					stream_controller.set_stream_url_if_changed(sm.stream_url)
					
					stream_controller.handle_stream_state(sm.stream_until)
				except Exception as e:
					print(e)
					pass # Do nothing, just skip this frame
except Exception as e:
	print(e)
finally:
	cleanly_close_program(None, None)