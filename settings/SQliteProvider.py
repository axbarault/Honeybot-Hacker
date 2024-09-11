from os import access, R_OK, W_OK
from os.path import exists
import sqlite3
from typing import Union

from log import *
from structures import NewbieUser, RootMeUser, SiteDbFunctions


class SQliteConnection(sqlite3.Connection):

	def cursor(self, cursorClass: type | None = ...) -> sqlite3.Cursor:
		return super(SQliteConnection, self).cursor(SQliteSession)


class SQliteSession(sqlite3.Cursor):

	LINK_NONE = 0
	LINK_DID = 1
	LINK_RID = 2

	################
	# VERIFICATION #
	################

	def create_discord_users_table(self):
		self.execute("""
				CREATE TABLE IF NOT EXISTS discord_users(
				d_id INT PRIMARY KEY NOT NULL,
				d_name TEXT NOT NULL
				)
			""")

	def is_verified(self, user_id: int) -> bool:
		query = "SELECT COUNT(*) FROM discord_users WHERE d_id=?"
		return self.execute(query, [user_id]).fetchall()[0][0] == 1

	def verify(self, user_id: int, username: str):
		query = "INSERT INTO discord_users (d_id, d_name) VALUES (?, ?)"
		self.execute(query, [user_id, username])

	##################
	# NEWBIE CONTEST #
	##################
	def create_newbie_users_table(self):
		self.execute("""
				CREATE TABLE IF NOT EXISTS newbie_users(
				d_id INT PRIMARY KEY NOT NULL,
				rm_id INT UNIQUE NOT NULL,
				rm_name TEXT NOT NULL,
				rm_pts INT NOT NULL,
				rm_pos INT NOT NULL,
				FOREIGN KEY (d_id) REFERENCES discord_users(d_id)
				);
			""")

	def link_newbie_user(self, user: NewbieUser):
		query = "INSERT INTO newbie_users(d_id, rm_id, rm_name, rm_pts, rm_pos) VALUES (?, ?, ?, ?, ?)"
		args = [user.d_id, user.rm_id, user.rm_name, user.rm_pts, user.rm_pos]
		self.execute(query, args)

	def unlink_newbie_user(self, user: NewbieUser):
		query = "DELETE FROM newbie_users WHERE d_id=?"
		self.execute(query, [user.d_id])

	def is_newbie_linked(self, d_id: Union[int, None] = None, rm_id: Union[int, None] = None) -> int:
		assert d_id is not None or rm_id is not None
		# Check for discord id
		if d_id is not None:
			query = "SELECT COUNT(*) FROM newbie_users WHERE d_id=?"
			if self.execute(query, [d_id]).fetchall()[0][0] >= 1:
				return self.LINK_DID
		# Check for remote id
		if rm_id is not None:
			query = "SELECT COUNT(*) FROM newbie_users WHERE rm_id=?"
			if self.execute(query, [rm_id]).fetchall()[0][0] >= 1:
				return self.LINK_RID
		return self.LINK_NONE

	def update_newbie_user(self, user: NewbieUser):
		query = "UPDATE newbie_users SET rm_pts=?, rm_pos=? WHERE d_id=?"
		self.execute(query, [user.rm_pts, user.rm_pos, user.d_id])

	def get_newbie_users(self) -> map:
		rows = self.execute("SELECT d.d_id, d.d_name, n.rm_id, n.rm_name, n.rm_pts, n.rm_pos FROM newbie_users n LEFT OUTER JOIN discord_users d ON d.d_id=n.d_id ORDER BY n.rm_pts DESC").fetchall()
		return map(lambda row: NewbieUser(d_id=row[0], d_name=row[1], rm_id=row[2], rm_name=row[3], rm_pts=row[4], rm_pos=row[5]), rows)

	def get_newbie_user(self, d_id: int) -> Union[None, NewbieUser]:
		rows = self.execute("SELECT d.d_id, d.d_name, n.rm_id, n.rm_name, n.rm_pts, n.rm_pos FROM newbie_users n LEFT OUTER JOIN discord_users d ON d.d_id=n.d_id WHERE d.d_id=?", [d_id]).fetchall()
		if len(rows) == 0:
			return None
		row = rows[0]
		return NewbieUser(d_id=row[0], d_name=row[1], rm_id=row[2], rm_name=row[3], rm_pts=row[4], rm_pos=row[5])

	NEWBIE_FUNCTION_SET = SiteDbFunctions(
		create_tables=create_newbie_users_table,
		link_user=link_newbie_user,
		unlink_user=unlink_newbie_user,
		check_linked=is_newbie_linked,
		update_user=update_newbie_user,
		get_users=get_newbie_users,
		get_user=get_newbie_user
	)

	###########
	# ROOT ME #
	###########

	def create_rootme_users_table(self):
		self.execute("""
				CREATE TABLE IF NOT EXISTS rootme_users(
				d_id INT PRIMARY KEY NOT NULL,
				rm_id INT UNIQUE NOT NULL,
				rm_name TEXT NOT NULL,
				rm_pts INT NOT NULL,
				rm_challs INT NOT NULL,
				rm_pos INT NOT NULL,
				rm_rank TEXT NOT NULL,
				FOREIGN KEY (d_id) REFERENCES discord_users(d_id)
				);
			""")

	def link_rootme_user(self, user: RootMeUser):
		query = "INSERT INTO rootme_users(d_id, rm_id, rm_name, rm_pts, rm_challs, rm_pos, rm_rank) VALUES (?, ?, ?, ?, ?, ?, ?)"
		args = [user.d_id, user.rm_id, user.rm_name, user.rm_pts, user.rm_challs, user.rm_pos, user.rm_rank]
		self.execute(query, args)

	def unlink_rootme_user(self, user: RootMeUser):
		query = "DELETE FROM rootme_users WHERE d_id=?"
		self.execute(query, [user.d_id])

	def is_rootme_linked(self, d_id: Union[int, None] = None, rm_id: Union[int, None] = None) -> int:
		assert d_id is not None or rm_id is not None
		# Check for discord id
		if d_id is not None:
			query = "SELECT COUNT(*) FROM rootme_users WHERE d_id=?"
			if self.execute(query, [d_id]).fetchall()[0][0] >= 1:
				return self.LINK_DID
		# Check for remote id
		if rm_id is not None:
			query = "SELECT COUNT(*) FROM rootme_users WHERE rm_id=?"
			if self.execute(query, [rm_id]).fetchall()[0][0] >= 1:
				return self.LINK_RID
		return self.LINK_NONE

	def update_rootme_user(self, user: RootMeUser):
		query = "UPDATE rootme_users SET rm_name=?, rm_pts=?, rm_challs=?, rm_pos=?, rm_rank=? WHERE d_id=?"
		self.execute(query, [user.rm_name, user.rm_pts, user.rm_challs, user.rm_pos, user.rm_rank, user.d_id])

	def get_rootme_users(self) -> map:
		rows = self.execute("SELECT d.d_id, d.d_name, rm.rm_id, rm.rm_name, rm.rm_pts, rm.rm_challs, rm.rm_pos, rm.rm_rank FROM rootme_users rm LEFT OUTER JOIN discord_users d ON d.d_id=rm.d_id ORDER BY rm.rm_pts DESC").fetchall()
		return map(lambda row: RootMeUser(d_id=row[0], d_name=row[1], rm_id=row[2], rm_name=row[3], rm_pts=row[4], rm_challs=row[5], rm_pos=row[6], rm_rank=row[7]), rows)

	def get_rootme_user(self, d_id: int) -> Union[None, RootMeUser]:
		rows = self.execute("SELECT d.d_id, d.d_name, rm.rm_id, rm.rm_name, rm.rm_pts, rm.rm_challs, rm.rm_pos, rm.rm_rank FROM rootme_users rm LEFT OUTER JOIN discord_users d ON d.d_id=rm.d_id WHERE d.d_id=?", [d_id]).fetchall()
		if len(rows) == 0:
			return None
		row = rows[0]
		return RootMeUser(d_id=row[0], d_name=row[1], rm_id=row[2], rm_name=row[3], rm_pts=row[4], rm_challs=row[5], rm_pos=row[6], rm_rank=row[7])

	ROOTME_FUNCTION_SET = SiteDbFunctions(
		create_tables=create_rootme_users_table,
		link_user=link_rootme_user,
		unlink_user=unlink_rootme_user,
		check_linked=is_rootme_linked,
		update_user=update_rootme_user,
		get_users=get_rootme_users,
		get_user=get_rootme_user
	)

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
