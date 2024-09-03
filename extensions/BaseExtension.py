from discord import Message
from discord.ext.commands import Bot

from sqlite3 import Cursor
from abc import ABC, abstractmethod
from typing import Any, Union, Callable, Coroutine

from command import Command, CommandMap
from settings import SettingsStore, SQliteProvider, SQliteSession


class BaseExtension(ABC):

	def __init__(self):
		self._commands = []

	@abstractmethod
	async def on_load(self, client: Bot):
		"""
		Called when the extension is loaded and applied to the bot instance
		:param client: The bot instance
		"""
		pass

	@staticmethod
	@abstractmethod
	def get_display_name() -> str:
		"""
		:return: The extension's display name, used for the logs and the help message
		"""
		pass

	@staticmethod
	@abstractmethod
	def get_short_name() -> str:
		"""
		:return: The extension's short name, used as a config prefix and internal representation
		"""
		pass

	@staticmethod
	@abstractmethod
	def get_description() -> str:
		"""
		:return: A short description giving more details about the extension
		"""
		pass

	@staticmethod
	@abstractmethod
	def get_author() -> str:
		"""
		:return: Extension author
		"""
		pass

	@staticmethod
	@abstractmethod
	def get_contributors() -> list[str]:
		"""
		:return: Extension contributors returned as a list
		"""
		pass

	@classmethod
	def get_extension_field(cls, field: str) -> str:
		"""
		Prepend the extension's short name to a setting field
		:param field: base name of the field
		:return: This extension's short name + The base name of the field
		"""
		return cls.get_short_name() + SettingsStore.field_separator + field

	@classmethod
	def register_extension_setting(cls, field: str, default: Any) -> bool:
		"""
		Register a default value for a given setting of this extension
		This should be called when the extension is initialized
		"""
		settings: SettingsStore = SettingsStore.get_instance()
		return settings.set_default(cls.get_extension_field(field), default)

	@classmethod
	def get_extension_setting(cls, field: str, default: Any = None) -> Any:
		"""
		Get the value of a setting associated to this extension
		If the setting doesn't exist, it WILL NOT be created and the default value will be returned instead.
		"""
		settings: SettingsStore = SettingsStore.get_instance()
		return settings.get(cls.get_extension_field(field), default)

	@classmethod
	def set_extension_setting(cls, field: str, value: Any):
		"""
		Set a value for a setting associated to this extension
		If the setting doesn't exist, it will be created with the given value
		"""
		settings: SettingsStore = SettingsStore.get_instance()
		return settings.set(cls.get_extension_field(field), value)

	def register_command(self, name: str, description: str, aliases: list[str], usage: Union[str, None], handler: Callable[[Message, list[str], Command], Coroutine]):
		commandObj = Command(name, self.get_display_name(), description, aliases, usage, handler)
		CommandMap.get_instance().register_command(commandObj)
		self._commands.append(commandObj)

	def get_commands(self) -> list[Command]:
		return self._commands


class SqlExtension(BaseExtension, ABC):

	def __init__(self):
		super().__init__()
		self.setup_tables()

	@staticmethod
	def new_session() -> SQliteSession:
		return SQliteProvider.get_instance().new_session()

	@abstractmethod
	def setup_tables(self) -> None:
		pass
