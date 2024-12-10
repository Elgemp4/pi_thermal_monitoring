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