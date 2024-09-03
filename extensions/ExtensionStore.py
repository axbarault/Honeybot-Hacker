from typing import Union
from extensions import BaseExtension
from log import info


class ExtensionStore:
	"""
	Singleton Class used to store commands
	"""
	_instance = None

	@staticmethod
	def get_instance():
		if ExtensionStore._instance is None:
			return ExtensionStore()
		return ExtensionStore._instance

	def __init__(self):
		if ExtensionStore._instance is not None:
			raise RuntimeError("Trying to instantiate a second instance of the ExtensionStore Singleton class")
		ExtensionStore._instance = self
		self._extensions = {}

	def register_extension(self, ext: BaseExtension):
		if self.extension_exists(ext.get_short_name()):
			raise NameError("Extension %s already exists" % ext.get_short_name())
		self._extensions[ext.get_short_name().lower()] = ext
		info("Extension Loaded : %s (%s)" % (ext.get_display_name(), ext.get_short_name()))

	def extension_exists(self, name: str) -> bool:
		return name.lower() in self._extensions

	def get_extension(self, name: str) -> Union[None, BaseExtension]:
		if not self.extension_exists(name):
			return None
		return self._extensions[name.lower()]

	def get_extensions(self) -> list[BaseExtension]:
		return list(self._extensions.values())
