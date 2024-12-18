import os
import time
import cv2
from linuxpy.video.device import Device, BufferType
import numpy as np

from image_processor import ImageProcessor

class CameraController():
	cap : cv2.VideoCapture = None
	dev : int = None
	camera_path : str = None

	image_processor : ImageProcessor

	def __init__(self):
		self.image_processor = ImageProcessor()

	def get_width(self) -> int:
		return self.image_processor.get_width()
	
	def get_height(self) -> int:
		return self.image_processor.get_height()

	def _scan_cameras(self) -> int:
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

	def _find_camera_device(self) -> None:
		while(self.dev == None):
			try:
				self.dev = self._scan_cameras()
				self.camera_path = '/dev/video'+str(self.dev)
				print(f"Camera found at {self.camera_path}")
			except Exception as e:
				print("Camera not found, retrying in 5 seconds")
				time.sleep(5)
		
	def connect_camera(self) -> None:
		self._find_camera_device()

		self.cap = cv2.VideoCapture(self.camera_path, cv2.CAP_V4L)
		self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)
	
	def handle_camera_reconnect(self) -> None:
		if(os.path.exists(self.camera_path) == False or self.cap.isOpened() == False):
			self.cap.release()
			time.sleep(1)
			
			self.dev = self._find_camera_device()
			self.camera_path = '/dev/video'+str(self.dev)

			self.cap.open(self.camera_path, cv2.CAP_V4L)
			self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)

	def get_frame_data(self) -> tuple[np.ndarray, np.ndarray]:
		(frame_acquired, frame) = self.cap.read()
		if not frame_acquired:
			self.handle_camera_reconnect()
			print("Failed to acquire frame")
			raise Exception("Failed to acquire frame")
		
		im_data, raw_th_data = np.array_split(frame, 2)
		th_data = self.convertRawToCelcius(raw_th_data)
		
		heatmap_image = self.image_processor.apply_color_map(im_data)

		return heatmap_image, th_data

	def release(self) -> None:
		self.cap.release()

	# Converting the raw values to celsius
	# https://www.eevblog.com/forum/thermal-imaging/infiray-and-their-p2-pro-discussion/200/
	# Huge props to LeoDJ for figuring out how the data is stored and how to compute temp from it.
	# Basically the temperatures are stored on 14 bits in kelvin multiplied by 16
	# As the data is stored on two different bytes they need to be recombined in a single 16 bits unsigned integer
	# So the formula is (raw_temp >> 2) / 16 to get the temperature in Kelvin
	# Then we substract 273.15 to convert Kelvin in Celcius
	# Simplified the equation become : raw_temp / 64 - 273.15
	# The data is then rounded for ease of use
	def convertRawToCelcius(self, raw_temp) -> np.ndarray:
		return np.round(((raw_temp[..., 1].astype(np.uint16) << 8) + raw_temp[..., 0].astype(np.uint16)) / 64 - 273.15, 2)