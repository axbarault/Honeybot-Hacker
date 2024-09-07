class NewbieUser:

	def __init__(self, **kwargs):
		self.d_id = kwargs.get('d_id', None)
		self.d_name = kwargs.get('d_name', None)
		self.n_id = kwargs.get('n_id', None)
		self.n_name = kwargs.get('n_name', None)
		self.n_pts = kwargs.get('n_pts', None)
		self.n_pos = kwargs.get('n_pos', None)
