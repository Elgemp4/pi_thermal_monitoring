import numpy as np

class Zone:
	def __init__(self, id, name, bottom, top, left, right):
		self.name = name
		self.id = id
		self.bottom = min(bottom, top)
		self.top = max(bottom, top)
		self.left = min(left, right)
		self.right = max(left, right)
		self.total_period = 0
		self.period_highest = -1000
		self.period_lowest = 1000
		self.total_period_count = 0

	def set_th_data(self, th_data):
		if(self.bottom == self.top or self.left == self.right):
			self.th_data = np.array([[0]])

		self.th_data = th_data[self.bottom:self.top, self.left:self.right]

	def compute_period(self):
		self.total_period += self.find_highest()[2]
		self.total_period_count += 1
		self.period_highest = max(self.period_highest, self.find_highest()[2])
		self.period_lowest = min(self.period_lowest, self.find_lowest()[2])


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
	
	def get_period_average(self):
		if self.total_period_count == 0:
			return 0
		return round(self.total_period / self.total_period_count, 2)
	
	def get_period_highest(self):
		return self.period_highest
	
	def get_period_lowest(self):
		return self.period_lowest
	
	def reset_period(self):
		self.total_period = 0
		self.total_period_count = 0
		self.period_highest = -1000
		self.period_lowest = 1000
	

