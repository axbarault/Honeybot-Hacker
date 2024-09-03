from command import Command
from typing import Union


class CommandMap:
	"""
	Singleton Class used to store commands
	"""
	_instance = None

	@staticmethod
	def get_instance():
		if CommandMap._instance is None:
			return CommandMap()
		return CommandMap._instance

	def __init__(self):
		if CommandMap._instance is not None:
			raise RuntimeError("Trying to instantiate a second instance of the CommandMap Singleton class")
		CommandMap._instance = self
		self._commands = {}
		self._aliases = {}

	def register_command(self, command: Command):
		if self.command_exists(command.get_name()):
			raise NameError("Command %s already exists" % command.get_name())
		low = command.get_name().lower()
		self._commands[low] = command
		self._aliases[low] = command
		for alias in command.get_aliases():
			if self.command_exists(alias):
				raise NameError("Command %s already exists" % command.get_name())
			self._aliases[alias.lower()] = command

	def command_exists(self, name: str) -> bool:
		low = name.lower()
		return low in self._commands or low in self._aliases

	def get_command(self, name: str) -> Union[None, Command]:
		if not self.command_exists(name):
			return None
		return self._aliases[name.lower()]
