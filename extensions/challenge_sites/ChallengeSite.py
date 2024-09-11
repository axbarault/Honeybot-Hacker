from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from datetime import datetime
from typing import TypeVar, Generic, Union

import requests
from discord import Embed, Guild

from extensions.ExtensionUtils import new_session
from settings import SQliteSession
from structures import SiteDbFunctions, SiteUser

T = TypeVar('T')


class ChallengeSite(Generic[T], ABC):
	ERR_LINK_NONE = 0  # No error occurred
	ERR_LINK_DID = 1  # Discord already linked to a remote account
	ERR_LINK_RID = 2  # Remote ID is already linked to a Discord account
	ERR_LINK_REMOTE_NA = 3  # Remote ID does not exist

	def __init__(self, site_name: str, aliases: list[str], avatar_url: str, site_fns: SiteDbFunctions[T],
	             scheduler: AbstractEventLoop, **kwargs):
		self.site_name = site_name
		self.aliases = aliases
		self.avatar_url = avatar_url
		self.site_color = int(kwargs.get('site_color', "0xAAAAAA"), 16)
		self.last_update: datetime = datetime.now()
		self.site_fns = site_fns
		self.scheduler = scheduler

		self.description = kwargs.get('description',
		                              f"Lie ton compte {site_name} à Discord et participe à la leaderboard du club!")
		self.short_name = kwargs.get('short_name', self.site_name.lower().replace(" ", ""))
		if self.short_name not in self.aliases:
			self.aliases.append(self.short_name)

	@abstractmethod
	def new_user_structure(self, **kwargs) -> T:
		"""
		Simply create a new user structure by passing **kwargs as its arguments
		:param kwargs: Keyword arguments to be passed to the structure
		:return: A user structure initialized with **kwargs
		"""
		pass

	@abstractmethod
	async def fetch_user_data(self, into: T) -> bool:
		"""
		Fetch user data from the website or its API
		:param into: User structure into witch to fill the parsed information
		:return: True on success, False on failure (if the user doesn't exist for example)
		"""
		pass

	@abstractmethod
	def get_user_url(self, user: T) -> str:
		"""
		Get a user's profile URL from a user object
		:param user: The user to get a URL to
		:return: URL
		"""
		pass

	@abstractmethod
	def get_failed_fetch_message(self, attempt: str) -> str:
		"""
		Message displayed when an account could not be resolved from the user input
		:param attempt: The user input
		:return: The message to be displayed
		"""
		pass

	async def request_webpage(self, url: str, cookies: Union[dict, None] = None) -> requests.Response:
		return await self.scheduler.run_in_executor(None, lambda: requests.get(url, cookies=cookies))

	async def link_account(self, user: T) -> int:
		"""
		Internal link_account function (Links a discord user to a remote site user)
		Requires every field from the specific SiteUser structure to be filled
		:param user: User structure containing all the information required by the database to create a new row
		:return: Error code
		"""
		assert isinstance(user, SiteUser) and user.assert_integrity()

		with new_session() as cursor:
			account_status = self.site_fns.check_linked(cursor, user.d_id, user.rm_id)

		if account_status == SQliteSession.LINK_DID:
			return self.ERR_LINK_DID
		if account_status == SQliteSession.LINK_RID:
			return self.ERR_LINK_RID

		with new_session() as cursor:
			self.site_fns.link_user(cursor, user)

		return self.ERR_LINK_NONE

	async def unlink_account(self, user: T) -> int:
		"""
		Internal unlink_account function (Unlinks a discord user from the remote site)
		Requires the discord id field from the SiteUser structure to be filled
		:return: Error code
		"""
		assert isinstance(user, SiteUser) and user.d_id is not None

		with new_session() as cursor:
			linked_acc = self.site_fns.check_linked(cursor, user.d_id, None)

		if linked_acc == SQliteSession.LINK_NONE:  # Account is not linked at all
			return self.ERR_LINK_DID  # We are missing a discord link

		with new_session() as cursor:  # Account is linked to discord, so we unlink it
			self.site_fns.unlink_user(cursor, user)

		return self.ERR_LINK_NONE

	def build_profile_embed(self, user: T) -> Embed:
		assert isinstance(user, SiteUser) and user.assert_integrity()
		embed = Embed()
		embed.set_author(name="Profile " + self.site_name, icon_url=self.avatar_url, url=self.get_user_url(user))
		embed.set_thumbnail(url=f"https://www.root-me.org/IMG/logo/auton{user.rm_id}.png")
		embed.colour = self.site_color
		user.fill_embed_fields(embed)
		return embed

	@abstractmethod
	def get_leaderboard_complement(self, user: T) -> str:
		"""
		Get additional leaderboard information about a user
		"""
		pass

	def build_leaderboard(self, guild: Guild) -> str:
		with new_session() as cursor:
			users = self.site_fns.get_users(cursor)
		medals = {0: '🥇', 1: '🥈', 2: '🥉'}
		return "\n".join([
			("%s %s ─ [%s](%s) ─ %d%s" % (
				(medals[i] if i in medals else f"#{i + 1}"),
				(user.d_name or user.rm_name) if guild.get_member(user.d_id) is None else f"<@{user.d_id}>",
				user.rm_name,
				self.get_user_url(user),
				user.rm_pts,
				self.get_leaderboard_complement(user)
			)) for i, user in enumerate(users)
		])
