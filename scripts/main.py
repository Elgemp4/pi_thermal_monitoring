#!/usr/bin/env python3

from pyvirtualcam import PixelFormat

import cv2
import pyvirtualcam
import numpy as np
import argparse
import io


#We need to know if we are running on the Pi, because openCV behaves a little oddly on all the builds!
#https://raspberrypi.stackexchange.com/questions/5100/detect-that-a-python-program-is-running-on-the-pi
def is_raspberrypi():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower(): return True
    except Exception: pass
    return False

isPi = is_raspberrypi()

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=int, default=1, help="Video Device number e.g. 0, use v4l2-ctl --list-devices")
args = parser.parse_args()
	
if args.device:
	dev = args.device
else:
	dev = 0
	
#init video

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


class Zone:
	def __init__(self, name, bottom, top, left, right):
		self.name = name
		self.bottom = bottom
		self.top = top
		self.left = left
		self.right = right

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

zones = [Zone("Zone 1", 0, 64, 0, 64), Zone("Zone 2", 0, 64, 64, 128), Zone("Zone 3", 0, 64, 128, 192), Zone("Zone 4", 64, 128, 0, 64), Zone("Zone 5", 128, 172, 128, 172)]

#data_write = csv.writer(open('data.csv', 'a'))
#time_for_next_write = time.time()

with pyvirtualcam.Camera(width, height, 25, fmt=PixelFormat.BGR, print_fps=25) as cam:
	print(f'Virtual cam started: {cam.device} ({cam.width}x{cam.height} @ {cam.fps}fps)')
	print("Before : ", cap.isOpened())
	while cap.isOpened():
		print("Inside : ", cap.isOpened())
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

			#for zone in zones:
			#	gui.draw_zone(image, zone, th_data, scale)
			print("Frame sent");
			cam.send(image);

	cap.release()