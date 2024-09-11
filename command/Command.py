from typing import Callable, Union
from discord import Message
from typing import Coroutine


class Command:

	def __init__(self, name: str, extension: str, description: str, aliases: list[str], usage: Union[str, None], handler: Callable[[Message, list[str]], Coroutine]):
		"""
		:param name: Command name
		:param extension: Nom de l'extension propriétaire de cette commande
		:param description: Command description
		:param usage: Message d'aide pour utiliser la commande
		:param aliases: Command aliases / alternative names
		:param handler: Command handler (async function taking the originating Message as well as a list of arguments as its parameters)
		"""
		self._name = name
		self._extension = extension
		self._description = description
		self._aliases = aliases
		self._usage = usage
		self._handler = handler

	def get_name(self) -> str:
		return self._name

	def get_extension(self) -> str:
		return self._extension

	def get_description(self) -> str:
		return self._description

	def get_aliases(self) -> list[str]:
		return self._aliases

	def get_usage(self) -> Union[str, None]:
		return self._usage

	def get_handler(self) -> Callable[[Message, list[str]], Coroutine]:
		return self._handler

	async def execute(self, origin: Message, args: list[str]):
		await self._handler(origin, args)

