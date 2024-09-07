
class RootMeUser:

	def __init__(self, **kwargs):
		self.d_id = kwargs.get('d_id', None)
		self.d_name = kwargs.get('d_name', None)
		self.rm_name = kwargs.get('rm_name', None)
		self.rm_points = kwargs.get('rm_points', None)
		self.rm_challenges = kwargs.get('rm_challs', None)
		self.rm_position = kwargs.get('rm_pos', None)

