#!/usr/bin/env python3

from pyvirtualcam import PixelFormat
from temperature import convertRawToCelcius
from system_utils import find_camera_device
from firebase_socket import SocketManager

import cv2
import pyvirtualcam
import numpy as np
import argparse
import time
import signal
import sys

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


def interrupt_handler(sig, frame):
	print("\nInterrupt received, exiting gracefully...")
	cap.release()
	sys.exit()

signal.signal(signal.SIGINT, interrupt_handler)


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

with pyvirtualcam.Camera(width, height, 25, fmt=PixelFormat.BGR, print_fps=25) as cam:
	print(f'Virtual cam started: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)')

	with SocketManager() as sm:
		next_time_to_send = time.time()
		while cap.isOpened():
			if(sm.listen_firebase() == False): #If the connection is closed,
				print("Connection closed")
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

				if(sm.measure_each != -1 and next_time_to_send < time.time()):
					data = {}
					print("Zones : " + str(sm.zone_list))
					print("Max temp : " + str(sm.max_temp))
					for zone in sm.zone_list:
						zone.set_th_data(th_data)
						(x,y,temp) = zone.find_highest()
						data[zone.id] = temp
					print(data)

					next_time_to_send = time.time() + sm.measure_each
					sm.send_temperature_data(data)

				cam.send(image)
	cap.release()