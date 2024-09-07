from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from extensions import UtilitiesExtension

from discord import Message
from discord.ext.commands import Bot

from asyncio import AbstractEventLoop
from abc import ABC, abstractmethod
from typing import Any, Union, Callable, Coroutine, final

from extensions import ExtensionStore
from command import Command, CommandMap
from settings import SettingsStore, SQliteProvider, SQliteSession


class BaseExtension(ABC):

	scheduler: AbstractEventLoop = None

	def __init__(self, display_name: str, short_name: str, description: str, author: str, contributors: list[str]):
		self._commands = []
		self.display_name = display_name
		self.short_name = short_name
		self.description = description
		self.author = author
		self.contributors = contributors

	@abstractmethod
	async def on_load(self, client: Bot):
		"""
		Called when the extension is loaded and applied to the bot instance
		:param client: The bot instance
		"""
		pass

	@final
	async def help(self, origin: Message, cmd_name: str):
		utilities: UtilitiesExtension = ExtensionStore.get_instance().get_extension('utilities')
		await utilities.help_command(origin, [cmd_name])

	@final
	def get_extension_field(self, field: str) -> str:
		"""
		Prepend the extension's short name to a setting field
		:param field: base name of the field
		:return: This extension's short name + The base name of the field
		"""
		return self.short_name + SettingsStore.fs + field

	@final
	def register_extension_setting(self, field: str, default: Any) -> bool:
		"""
		Register a default value for a given setting of this extension
		This should be called when the extension is initialized
		"""
		settings: SettingsStore = SettingsStore.get_instance()
		return settings.set_default(self.get_extension_field(field), default)

	@final
	def get_extension_setting(self, field: str, default: Any = None) -> Any:
		"""
		Get the value of a setting associated to this extension
		If the setting doesn't exist, it WILL NOT be created and the default value will be returned instead.
		"""
		settings: SettingsStore = SettingsStore.get_instance()
		return settings.get(self.get_extension_field(field), default)

	@final
	def set_extension_setting(self, field: str, value: Any):
		"""
		Set a value for a setting associated to this extension
		If the setting doesn't exist, it will be created with the given value
		"""
		settings: SettingsStore = SettingsStore.get_instance()
		return settings.set(self.get_extension_field(field), value)

	async def register_command(self, name: str, description: str, aliases: list[str], usage: Union[str, None], handler: Callable[[Message, list[str], Command], Coroutine]):
		commandObj = Command(name, self.display_name, description, aliases, usage, handler)
		CommandMap.get_instance().register_command(commandObj)
		self._commands.append(commandObj)

	def get_commands(self) -> list[Command]:
		return self._commands


class SqlExtension(BaseExtension, ABC):

	def __init__(self, display_name: str, short_name: str, description: str, author: str, contributors: list[str]):
		super().__init__(display_name, short_name, description, author, contributors)
		self.setup_tables()

	@staticmethod
	def new_session() -> SQliteSession:
		return SQliteProvider.get_instance().new_session()

	@abstractmethod
	def setup_tables(self) -> None:
		pass


# class ChallengeSiteExtension(SqlExtension, ABC):
#
# 	def __init__(self, site_name: str, site_initials: str, site_avatar: str):
# 		super().__init__()
# 		self.site_name = site_name
# 		self.site_short_name = site_name.replace(" ", "").lower()
# 		self.site_initials = site_initials
# 		self.site_avatar = site_avatar
# 		self.last_update = datetime.now()
#
# 	async def on_load(self, client: Bot):
# 		# Link Command
# 		self.register_command(
# 			f'link{self.site_short_name}'
# 		)
#
# 	@staticmethod
# 	@abstractmethod
# 	def link_user(cursor: SQliteProvider, user):
# 		"""
# 		Performs the required operations to insert a new discord link into the database
# 		:param cursor: A db cursor
# 		:param user: A user structure
# 		"""
# 		pass
#
# 	@staticmethod
# 	@abstractmethod
# 	def unlink_user(cursor: SQliteProvider, d_id: int):
# 		"""
# 		Performs the required operations to remove a discord link from the database
# 		:param cursor: A db cursor
# 		:param d_id: The discord id to unlink
# 		"""
# 		pass





