import time
from linuxpy.video.device import Device, BufferType

def _find_camera_device():
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

def find_camera_device():
	dev = None	

	while(dev == None):
		try:
			dev = _find_camera_device()
		except Exception as e:
			print("Camera not found, retrying in 5 seconds")
			time.sleep(5)

	return dev