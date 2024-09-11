from __future__ import annotations
from typing import Callable, Any, TypeVar, Generic, TYPE_CHECKING, Union, Iterable

if TYPE_CHECKING:
	from settings import SQliteSession

T = TypeVar('T')


class SiteDbFunctions(Generic[T]):
	"""
	Collection of database operations needed to keep website users up-to-date
	Generic type T is a specific UserStructure accepted as argument by those functions
	"""

	def __init__(
			self,
			create_tables: Callable[[SQliteSession], Any],
			link_user: Callable[[SQliteSession, T], Any],
			unlink_user: Callable[[SQliteSession, T], Any],
			check_linked: Callable[[SQliteSession, Union[int, None], ...], int],
			update_user: Callable[[SQliteSession, T], Any],
			get_users: Callable[[SQliteSession], Iterable[T]],
			get_user: Callable[[SQliteSession, int], Union[None, T]]
	):
		self.create_tables = create_tables
		self.link_user = link_user
		self.unlink_user = unlink_user
		self.check_linked = check_linked
		self.update_user = update_user
		self.get_users = get_users
		self.get_user = get_user
