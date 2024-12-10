import numpy as np

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
	return np.round(((raw_temp[..., 1].astype(np.uint16) << 8) + raw_temp[..., 0].astype(np.uint16)) / 64 - 273.15, 2)