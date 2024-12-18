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
	

