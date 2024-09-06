from os import access, R_OK, W_OK
from os.path import exists
import sqlite3
from log import *
from structures import NewbieUser


class SQliteConnection(sqlite3.Connection):

	def cursor(self, cursorClass: type | None = ...) -> sqlite3.Cursor:
		return super(SQliteConnection, self).cursor(SQliteSession)


class SQliteSession(sqlite3.Cursor):

	################
	# VERIFICATION #
	################

	def create_discord_users_table(self):
		self.execute("""
				CREATE TABLE IF NOT EXISTS discord_users(
				discord_id INT PRIMARY KEY NOT NULL,
				discord_name TEXT NOT NULL
				)
			""")

	def is_verified(self, user_id: int) -> bool:
		query = "SELECT COUNT(*) FROM discord_users WHERE discord_id=?"
		return self.execute(query, [user_id]).fetchall()[0][0] == 1

	def verify(self, user_id: int, username: str):
		query = "INSERT INTO discord_users(discord_id, discord_name) VALUES (?, ?)"
		self.execute(query, [user_id, username])

	##################
	# NEWBIE CONTEST #
	##################
	def create_newbie_users_table(self):
		self.execute("""
				CREATE TABLE IF NOT EXISTS newbie_users(
				discord_id INT PRIMARY KEY NOT NULL,
				newbie_id INT UNIQUE NOT NULL,
				newbie_name TEXT NOT NULL,
				newbie_points INT NOT NULL,
				newbie_position INT NOT NULL,
				FOREIGN KEY (discord_id) REFERENCES discord_users(discord_id)
				);
			""")

	def link_newbie_user(self, d_id: int, n_id: int, n_name: str, n_points: int, n_position: int):
		query = "INSERT INTO newbie_users(discord_id, newbie_id, newbie_name, newbie_points, newbie_position) VALUES (?, ?, ?, ?, ?)"
		args = [d_id, n_id, n_name, n_points, n_position]
		self.execute(query, args)

	def unlink_newbie_user(self, d_id: int):
		query = "DELETE FROM newbie_users WHERE discord_id=?"
		self.execute(query, [d_id])

	def is_newbie_linked(self, **kwargs):
		if kwargs.get('d_id', None) is not None:
			query = "SELECT COUNT(*) FROM newbie_users WHERE discord_id=?"
			args = [kwargs.get('d_id')]
		elif kwargs.get('n_id', None) is not None:
			query = "SELECT COUNT(*) FROM newbie_users WHERE newbie_id=?"
			args = [kwargs.get('n_id')]
		else:
			raise ValueError('One of d_id and n_id keyword argument must be set')
		return self.execute(query, args).fetchall()[0][0] == 1

	def update_newbie_user(self, d_id: int, n_points: int, n_position: int):
		query = "UPDATE newbie_users SET newbie_points=?, newbie_position=? WHERE discord_id=?"
		self.execute(query, [n_points, n_position, d_id])

	def get_newbie_users(self) -> map:
		rows = self.execute("SELECT d.discord_id, d.discord_name, n.newbie_id, n.newbie_name, n.newbie_points, n.newbie_position FROM newbie_users n LEFT OUTER JOIN main.discord_users d ON d.discord_id=n.discord_id ORDER BY n.newbie_points DESC").fetchall()
		return map(lambda row: NewbieUser(*row), rows)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_val is not None:
			error(exc_val)
			error(exc_tb)
		self.connection.commit()
		self.connection.close()


class SQliteProvider:
	"""
	Singleton Class used to access extension settings
	"""
	_instance = None

	@staticmethod
	def get_instance() -> 'SQliteProvider':
		if SQliteProvider._instance is None:
			raise RuntimeError("SQliteProvider Singleton instance has not been initialized yet")
		return SQliteProvider._instance

	def __init__(self, path: str):
		"""
		:param path: Absolute path to the `config.json` resource file
		"""
		if SQliteProvider._instance is not None:
			raise RuntimeError("Trying to instantiate a second instance of the SQliteProvider Singleton class")
		if not exists(path):
			open(path, 'a').close()
		if not access(path, R_OK | W_OK):
			raise PermissionError("Missing reading or writing permissions on the passed sql file at path %s" % path)

		SQliteProvider._instance = self
		self._path = path

	def new_session(self) -> SQliteSession:
		cursor: SQliteSession = sqlite3.connect(self._path, factory=SQliteConnection).cursor(cursorClass=SQliteConnection)
		return cursor
