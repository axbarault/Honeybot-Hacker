import asyncio
import random
from datetime import datetime
from typing import Callable, Union, Any

from discord import Message, Embed, SelectOption, Interaction, Guild
from discord.ext import tasks
from discord.ext.commands import Bot
from discord.ui import View, Select

from extensions import SqlExtension
from extensions.ExtensionUtils import new_session
from extensions.challenge_sites import *
from log import error
from settings import SQliteSession
from structures import SiteUser


class SiteLeaderboardsExtension(SqlExtension):

	def __init__(self):
		super().__init__(
			display_name="Site Leaderboards",
			short_name="lbs",
			description="Intègre des classements locaux pour des sites de challenges comme RootMe et NewbieContest",
			author="MisTurtle",
			contributors=[]
		)
		self.register_extension_setting("rootme_api_key", "###")
		self.last_update = datetime.now()
		self.sites = []

	def setup_tables(self) -> None:
		for site in self.sites:
			with new_session() as cursor:
				site.site_fns.create_tables(cursor)

	async def on_load(self, client: Bot):
		# Init sites with client scheduler (This is not very pretty and a way to access the scheduler from elsewhere should be found)
		self.sites: list[ChallengeSite] = [
			NewbieContestSite(client.loop),
			RootMeSite(self.get_extension_setting("rootme_api_key"), client.loop)
		]

		# Setup database tables for all sites
		self.setup_tables()

		# Start auto update loop
		self.refresh_all.start()

		# Register commands
		await self.register_command(
			name="link",
			description="Lie ton compte Discord à un site supporté par le club",
			aliases=["ln"],
			usage="$ln <site> <pseudo>\n$ln newbie <pseudo>\n$ln rootme <pseudo>",
			handler=self.link_account_request
		)
		await self.register_command(
			name="unlink",
			description="Déconnecte ton compte Discord d'un site supporté par le club",
			aliases=["uln"],
			usage="$uln <site>\n$uln newbie\n$uln rootme",
			handler=self.unlink_account_request
		)
		await self.register_command(
			name="top",
			description="Affiche la leaderboard pour un site de challenge",
			aliases=["classement", "leaderboard", "lb"],
			usage="$top [site]",
			handler=self.leaderboard_request
		)
		await self.register_command(
			name="profile",
			description="Inspecte en détail ton profile sur l'un des sites de challenges lié à ton compte Discord",
			aliases=["p"],
			usage="$p [site]",
			handler=self.profile_request
		)

	def filter_sites(self, filter_fn: Callable[[ChallengeSite], bool]) -> list[ChallengeSite]:
		return list(filter(filter_fn, self.sites))

	def get_linked_sites(self, d_id: int) -> list[ChallengeSite]:
		def _(x: ChallengeSite):
			with new_session() as cursor:
				site_linked = x.site_fns.check_linked(cursor, d_id, None)
			return site_linked == SQliteSession.LINK_DID
		return self.filter_sites(_)

	def get_unlinked_sites(self, d_id: int) -> list[ChallengeSite]:
		def _(x: ChallengeSite):
			with new_session() as cursor:
				site_linked = x.site_fns.check_linked(cursor, d_id, None)
			return site_linked == SQliteSession.LINK_NONE
		return self.filter_sites(_)

	def site_from_alias(self, alias: str) -> Union[ChallengeSite, None]:
		for site in self.sites:
			if alias.lower() in site.aliases:
				return site
		return None

	async def link_account_request(self, origin: Message, args: list[str]):
		"""
		Called when a user runs the $link command
		"""
		# Check argument count
		if len(args) < 2:
			await self.help(origin, "ln")
			return
		# Check if the author has already linked all of their accounts
		d_id = origin.author.id

		unlinked_sites = self.get_unlinked_sites(d_id)
		if len(unlinked_sites) == 0:
			await origin.reply("Woops... On dirait que tu as déjà lié ton compte Discord à tous les sites supportés actuellement !\nPour déconnecter un compte, utilise la commande ``$uln <site>``")
			return

		# Check if the specified site exists
		site = self.site_from_alias(args[0])
		if site is None:
			supported_names = "**, **".join(map(lambda x: x.aliases[0], unlinked_sites))
			await origin.reply(f"Hmmm... Aucun site ne correspond à ``{args[0].lower()}``. Essaye plutôt un de ceux là: **" + supported_names + "**")
			return
		# Create a new partially filled user structure
		attempt = " ".join(args[1:])
		user: SiteUser = site.new_user_structure(
			d_id=d_id,
			d_name=origin.author.display_name,
			rm_id=int(attempt) if attempt.isnumeric() else None,
			rm_name=attempt if not attempt.isnumeric() else None
		)
		# Check that we have at least an id or a name to work with (The following condition should never be True, but we never know)
		if user.rm_id is None and user.rm_name is None:
			await origin.reply(f"Uh oh... Une erreur qui n'est vraiment pas censée se passer vient d'apparaître. Prévient un admin pour qu'on fixe le problème 😱")
			return
		# Fetch user data from the website
		fetch_result = await site.fetch_user_data(user)
		if not fetch_result:
			await origin.reply(site.get_failed_fetch_message(attempt))
			return
		# Try to proceed with the linking phase
		code = await site.link_account(user)
		if code == site.ERR_LINK_DID:
			await origin.reply(f"Ah... Ton compte Discord est déjà lié à un profile sur ce site. Exécute ``$uln {site.aliases[0]}`` et retente après.")
			return
		if code == site.ERR_LINK_RID:
			await origin.reply(f"Eheh, petit malin, ce profile est déjà lié à un autre compte Discord. Si c'est bien le tiens, contact un admin. Sinon, bien tenté, mais non ^^")
			return
		emojis = ["💯", "🎉", "🥳", "💪", "🍭"]
		await origin.reply(f"Parfait {emojis[random.randint(0, len(emojis) - 1)]} Ton compte {site.site_name} a été lié à Discord:", embed=site.build_profile_embed(user))

	async def unlink_account_request(self, origin: Message, args: list[str]):
		"""
		Called when a user runs the $unlink command
		"""
		# Check argument count
		if len(args) != 1:
			await self.help(origin, "uln")
			return
		# Check if the author has already linked any of their accounts
		d_id = origin.author.id

		linked_sites = self.get_linked_sites(d_id)
		if len(linked_sites) == 0:
			await origin.reply("Woops... On dirait que tu n'as pas encore lié ton compte Discord à un site de challenge !\nPour connecter un compte, utilise la commande ``$ln <site> <pseudo|id>``")
			return

		# Check if the specified site exists
		site = self.site_from_alias(args[0])
		if site is None:
			supported_names = "**, **".join(map(lambda x: x.aliases[0], linked_sites))
			await origin.reply(f"Hmmm... Aucun site ne correspond à ``{args[0].lower()}``. Essaye plutôt un de ceux là: **" + supported_names + "**")
			return

		# Create a new partially filled user structure
		user: SiteUser = site.new_user_structure(d_id=d_id)
		unlink_result = await site.unlink_account(user)
		if unlink_result == site.ERR_LINK_DID:
			await origin.reply(f"Ah! Ton compte Discord n'est pas encore lié à {site.site_name}! Utilise ``$ln {site.aliases[0]} <pseudo>`` pour t'y connecter.")
			return

		emojis = ["💯", "🎉", "🥳", "💪", "🍭"]
		await origin.reply(f"Et voilà {emojis[random.randint(0, len(emojis) - 1)]} Le profile {site.site_name} a été déconnecté de ton compte Discord.")

	# LEADERBOARD #
	async def leaderboard_request(self, origin: Message, args: list[str]):
		if len(self.sites) == 0:
			return  # Never happens
		target_site = None
		if len(args) > 0:
			target_site = self.site_from_alias(args[0].lower())
		if not isinstance(target_site, ChallengeSite):
			target_site = self.sites[0]

		await origin.reply(
			embed=self.build_leaderboard_embed(origin.guild, target_site),
			view=SiteSelectView(
				sites=self.sites,
				author_id=origin.author.id,
				handler=self.leaderboard_interaction_handler,
				default_site=target_site
			)
		)

	async def leaderboard_interaction_handler(self, _message: Message, author_id: int, _site: str):
		_target_site = self.site_from_alias(_site)
		if _target_site is None:
			return  # Shouldn't happen
		await _message.edit(
			content="",
			embed=self.build_leaderboard_embed(_message.guild, _target_site),
			view=SiteSelectView(self.sites, author_id, self.leaderboard_interaction_handler, _target_site)
		)

	def build_leaderboard_embed(self, guild: Guild, target_site: ChallengeSite) -> Embed:
		embed = Embed()
		embed.set_author(name=f"Classement {target_site.site_name} ─ {guild.name}", icon_url=target_site.avatar_url)
		embed.colour = target_site.site_color
		embed.description = target_site.build_leaderboard(guild)
		embed.timestamp = self.last_update
		embed.set_footer(text="Dernière mise à jour")
		return embed

	# PROFILE #
	async def profile_request(self, origin: Message, args: list[str]):
		"""
		Called when a user runs $profile
		"""
		d_id = origin.author.id

		linked_sites = self.get_linked_sites(d_id)
		if len(linked_sites) == 0:
			await origin.reply("Woops... On dirait que tu n'as pas encore lié ton compte Discord à un site de challenge !\nPour connecter un compte, utilise la commande ``$ln <site> <pseudo|id>``")
			return

		target_site = None
		if len(args) > 0:
			target_site = self.site_from_alias(args[0].lower())
			if target_site is None:
				supported_names = "**, **".join(map(lambda x: x.aliases[0], linked_sites))
				await origin.reply(f"Hmmm... Aucun site ne correspond à ``{args[0].lower()}``. Essaye plutôt un de ceux là: **" + supported_names + "**")
				return
			if target_site not in linked_sites:
				await origin.reply(f"Ah! Ton compte Discord n'est pas encore lié à {target_site.site_name}! Utilise ``$ln {target_site.aliases[0]} <pseudo>`` pour t'y connecter.")
				return

		if not isinstance(target_site, ChallengeSite):
			target_site = linked_sites[0]

		# Fetch user information
		with new_session() as cursor:
			user = target_site.site_fns.get_user(cursor, d_id)

		if user is None:  # Shouldn't happen since we already checked the site was linked
			await origin.reply("Huh... On dirait qu'il y a eu un problème en récupérant tes informations.\nPour connecter un compte, utilise la commande ``$ln <site> <pseudo|id>``")
			return

		if len(linked_sites) == 1:
			await origin.reply(embed=self.build_profile_embed(target_site, user))
		else:
			await origin.reply(
				embed=self.build_profile_embed(target_site, user),
				view=SiteSelectView(linked_sites, origin.author.id, self.profile_interaction_handler, target_site)
			)

	def build_profile_embed(self, _site: ChallengeSite, _user: SiteUser):
		embed = _site.build_profile_embed(_user)
		embed.timestamp = self.last_update
		embed.set_footer(text="Dernière mise à jour")
		return embed

	async def profile_interaction_handler(self, _message: Message, author_id: int, _site: str):
		_target_site = self.site_from_alias(_site)
		_linked_sites = self.get_linked_sites(author_id)
		if _target_site is None or _target_site not in _linked_sites:
			# Should only be called if a user unlinks their account while browsing their profile
			await _message.edit(content=f"Woops, on dirait que ton compte n'est plus lié à ce site ! Essaye ``$ln {_site} <pseudo>`` pour t'y reconnecter.", embed=None, view=None)
			return
		with new_session() as cursor:
			user = _target_site.site_fns.get_user(cursor, author_id)
		await _message.edit(
			content="",
			embed=self.build_profile_embed(_target_site, user),
			view=SiteSelectView(_linked_sites, author_id, self.profile_interaction_handler, _target_site) if len(_linked_sites) > 1 else None
		)

	@tasks.loop(minutes=120)
	async def refresh_all(self):
		"""
		Refresh database information
		"""
		for site in self.sites:
			with new_session() as cursor:
				users = site.site_fns.get_users(cursor)
			for user in users:
				if not await site.fetch_user_data(user):
					error("Failed to update %s's %s profile. Current data : %s" % (user.rm_name, site.site_name, str(user.__dict__)))
					continue
				with new_session() as cursor:
					site.site_fns.update_user(cursor, user)
				await asyncio.sleep(0.5)
		self.last_update = datetime.now()


class SiteSelect(Select):

	def __init__(self, handler: Callable[[Message, int, str], Any], author_id: int, **kwargs):
		super().__init__(**kwargs)
		self.handler = handler
		self.author_id = author_id

	async def callback(self, interaction: Interaction):
		await interaction.response.defer()
		await self.handler(interaction.message, self.author_id, self.values[0])


class SiteSelectView(View):

	def __init__(self, sites: list[ChallengeSite], author_id: int, handler: Callable, default_site: Union[ChallengeSite, None] = None):
		super().__init__(timeout=None)
		self.author_id = author_id
		self.add_item(SiteSelect(
			handler,
			author_id,
			min_values=1,
			max_values=1,
			options=[SelectOption(label=site.site_name, default=(i == 0) if default_site is None else (site == default_site), value=site.aliases[0]) for i, site in enumerate(sites)]
		))

	async def interaction_check(self, interaction: Interaction, /) -> bool:
		return interaction.user.id == self.author_id


