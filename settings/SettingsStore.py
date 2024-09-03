import json
import os
from os.path import exists
from os import access, R_OK, W_OK
from typing import Any


class SettingsStore:
	"""
	Singleton Class used to access extension settings
	"""
	_instance = None

	@staticmethod
	def get_instance():
		if SettingsStore._instance is None:
			raise RuntimeError("SettingsStore Singleton instance has not been initialized yet")
		return SettingsStore._instance

	field_separator = '.'

	def __init__(self, path: str):
		"""
		:param path: Absolute path to the `config.json` resource file
		"""
		if SettingsStore._instance is not None:
			raise RuntimeError("Trying to instantiate a second instance of the SettingsStore Singleton class")
		if not exists(path):
			os.makedirs(os.path.dirname(path), exist_ok=True)
			with open(path, 'w') as settings_file:
				print("An empty config file was created at the following path : %s" % path)
				settings_file.write('{}')
		if not access(path, R_OK | W_OK):
			raise PermissionError("Missing reading or writing permissions on the passed config file at path %s" % path)

		SettingsStore._instance = self
		self._path = path
		with open(path, 'r') as settings_file:
			self._settings = json.loads(settings_file.read())

	def get(self, field: str, default: Any = None) -> Any:
		"""
		Get a setting from its nested path in the config

		:param field: Nested field path (e.i. newbie.table_name)
		:param default: Default value returned in case the setting doesn't exist
		:return: The setting value
		"""
		field = field.split(SettingsStore.field_separator)
		nested = self._settings
		for key in field:
			if key not in nested:
				return default
			nested = nested[key]
		return nested

	def set(self, field: str, value: Any) -> None:
		"""
		Set a setting at the nested path in the config
		- If the setting doesn't exist, it will be created
		- If the setting already exists, it WILL be overwritten

		:param field: Nested field path (e.i. newbie.table_name)
		:param value: Value to replace the setting with
		"""
		field = field.split(SettingsStore.field_separator)
		nested = self._settings
		for key in field[:-1]:
			nested = nested.setdefault(key, {})
		nested[field[-1]] = value
		self.save()

	def set_default(self, field: str, value: Any) -> bool:
		"""
		Set a setting at the nested path in the config
		- If the setting doesn't exist, it will be created
		- If it exists, it's value WILL NOT be overwritten

		:param field: Nested field path (e.i. newbie.table_name)
		:param value: Value to replace the setting with
		:return: True if the setting was created, False if it already existed
		"""
		field = field.split(SettingsStore.field_separator)
		nested = self._settings
		for key in field[:-1]:
			nested = nested.setdefault(key, {})
		if field[-1] in nested:
			return False
		nested[field[-1]] = value
		self.save()
		return True

	def save(self) -> None:
		with open(self._path, 'w') as settings_file:
			settings_file.write(json.dumps(self._settings, indent=4))
