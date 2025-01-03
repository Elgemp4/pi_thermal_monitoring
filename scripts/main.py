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
import subprocess
import threading

camera_controller = CameraController()
stream_controller = VideoStreamController()

stop_event = threading.Event()
thread = None

next_time_to_send = time.time()

time_for_next_alert = 0
time_for_next_log = 0
over_limit = 0

all_camera = Zone("all", "all", 0, 192, 0, 256)

def cleanly_close_program(sig, frame):
	print("\nExiting gracefully...")
	camera_controller.release()
	stream_controller.stop_stream()
	if(thread is not None):
		stop_event.set()
		thread.join()
	sys.exit()

signal.signal(signal.SIGINT, cleanly_close_program)
signal.signal(signal.SIGTERM, cleanly_close_program)

def handle_temperature_data(sm : SocketManager, th_data : list) -> None:
	global next_time_to_send

	for zone in sm.zone_list:
		zone.set_th_data(th_data)
		zone.compute_period()

	if(sm.measure_each != -1 and next_time_to_send < time.time()):
		data = {}
		print("Sending temperature data")
		for zone in sm.zone_list:
			data[zone.id] = {
				"avg": zone.get_period_average(),
				"max": zone.get_period_highest(),
				"min": zone.get_period_lowest()
			}
			zone.reset_period()
	
		next_time_to_send = time.time() + sm.measure_each

		sm.send_temperature_data(data)

def handle_alerts(sm : SocketManager, th_data : list) -> None:
	global over_limit
	global time_for_next_alert
	global all_camera

	all_camera.set_th_data(th_data)

	(x,y,temp) = all_camera.find_highest()
	
	if(temp >= sm.max_temp and sm.max_temp != -1):
		over_limit += 1
	else:
		over_limit = -1

	if(over_limit >= 5):
		if(time_for_next_alert < time.time()):
			sm.send_alert(temp)
			time_for_next_alert = time.time() + 30

def get_logs(service_name, lines=10000):
	try:
		log_command = ['journalctl', '-u', service_name, '--no-pager']
		log_result = subprocess.run(log_command, capture_output=True, text=True)
		logs = log_result.stdout.splitlines()[:lines]
		return '\n'.join(logs)
	except Exception as e:
		return "Error while getting logs"
	
	
    
def listen_for_logs(sm: SocketManager):
	global time_for_next_log

	if(time_for_next_log > time.time()):
		return
	
	try:
		if(sm.output_logs):
			sm.send_log(get_logs("thermal_camera.service"))
	except Exception as e:	
		print(e)

	time_for_next_log = time.time() + 10
try:
	

	with pyvirtualcam.Camera(camera_controller.get_width(), camera_controller.get_height(), 25, fmt=PixelFormat.BGR) as virtual_camera:
		print(f'Virtual cam started: {virtual_camera.device} ({virtual_camera.width}x{virtual_camera.height} @ {virtual_camera.fps}fps)')
		with SocketManager() as sm:
			#thread = threading.Thread(target=listen_for_logs, args=(sm, stop_event))
			#thread.start()
			camera_controller.connect_camera()
			while True:
				sm.listen_firebase()

				try:
					listen_for_logs(sm)

					if(camera_controller.available_at is None or camera_controller.available_at > time.time()):
						continue;

					heatmap_image, th_data = camera_controller.get_frame_data()

					handle_alerts(sm, th_data)
					
					handle_temperature_data(sm, th_data)

					virtual_camera.send(heatmap_image)

					stream_controller.set_stream_url_if_changed(sm.stream_url)
					
					stream_controller.handle_stream_state(sm.stream_until, sm.stream_key)
				except Exception as e:
					print(e)
					pass # Do nothing, just skip this frame
except Exception as e:
	print(e)
finally:
	cleanly_close_program(None, None)