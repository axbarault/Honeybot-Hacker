import re
from asyncio import sleep, AbstractEventLoop
import requests
from datetime import datetime

from discord import Message, Embed
from discord.ext import commands, tasks

from command import Command
from extensions import SqlExtension, UtilitiesExtension


class NewbieExtension(SqlExtension):

	avatar_url: str = None
	scheduler: AbstractEventLoop = None
	last_update: datetime = None

	async def on_load(self, client: commands.Bot):
		NewbieExtension.avatar_url = "https://www.newbiecontest.org/images/logo.png"
		NewbieExtension.scheduler = client.loop
		NewbieExtension.last_update = datetime.now()

		self.register_command(
			name='linknewbie',
			description='Lie ton compte Discord à ton profile NewbieContest',
			aliases=['ln', 'newbie'],
			usage='$ln <pseudo newbie>',
			handler=NewbieExtension.link_newbie_account
		)
		self.register_command(
			name='unlinknewbie',
			description='Déconnecte ton compte Discord de ton profile NewbieContest',
			aliases=['uln'],
			usage='$uln <pseudo newbie>',
			handler=NewbieExtension.unlink_newbie_account
		)
		self.register_command(
			name='top',
			description='Déconnecte ton compte Discord de ton profile NewbieContest',
			aliases=['classement', 'rank'],
			usage=None,
			handler=NewbieExtension.show_leaderboard
		)

		NewbieExtension.refresh_all.start()

	def setup_tables(self) -> None:
		with self.new_session() as cursor:
			cursor.create_newbie_users_table()

	@staticmethod
	async def fetch_newbie_id(newbie_name: str) -> int | None:
		url = "https://www.newbiecontest.org/index.php?page=classementdynamique&member=%s&nosmiley=1" % newbie_name
		leaderboard = await NewbieExtension.scheduler.run_in_executor(None, lambda: requests.get(url))

		p_id = re.compile("Recherche de.*id=(\d+)")
		try:
			n_id = int(p_id.findall(leaderboard.text)[0])
			return n_id
		except IndexError:
			return None

	@staticmethod
	async def fetch_newbie_data(newbie_id: int) -> tuple | None:
		url = "https://www.newbiecontest.org/index.php?page=info_membre&id=%d" % newbie_id
		profile = await NewbieExtension.scheduler.run_in_executor(None, lambda: requests.get(url))
		profile = profile.text

		p_login = re.compile("Informations sur.*>\s*(.+?)(?:&nbsp|</span></a>)")
		p_points = re.compile("Points :.*>\s*(\d+)")
		p_position = re.compile("Position :.*>\s*(\d+)")

		try:
			login = p_login.findall(profile)[0]
			points = int(p_points.findall(profile)[0])
			position = int(p_position.findall(profile)[0])
		except IndexError:
			return None

		return login, points, position

	@staticmethod
	async def link_newbie_account(origin: Message, args: list[str], cmd: Command):
		if len(args) == 0:
			return await UtilitiesExtension.help_command(origin, [cmd.get_name()], cmd)

		with NewbieExtension.new_session() as cursor:
			has_account = cursor.is_newbie_linked(d_id=origin.author.id)
		if has_account:
			return await origin.reply('Ton compte discord est déjà lié à un profile NewbieContest!\nUtilise ``$uln`` pour te déconnecter et réessaye après')

		username = ' '.join(args)
		newbie_id = await NewbieExtension.fetch_newbie_id(username)
		if newbie_id is None:
			return await origin.reply('Aucun compte NewbieContest n\'est reconnu sous le pseudo %s' % username)

		with NewbieExtension.new_session() as cursor:
			alr_linked = cursor.is_newbie_linked(n_id=newbie_id)
		if alr_linked:
			return await origin.reply('Ce profile NewbieContest est déjà lié à un compte Discord!\nContact un admin si tu es le propriétaire de ce compte. Sinon, bien tenté, mais non ^^')

		newbie_data = await NewbieExtension.fetch_newbie_data(newbie_id)
		if newbie_data is None:
			return await origin.reply('Aucun compte NewbieContest n\'est reconnu sous le pseudo %s' % username)

		with NewbieExtension.new_session() as cursor:
			cursor.link_newbie_user(origin.author.id, newbie_id, newbie_data[0], newbie_data[1], newbie_data[2])
		await origin.reply('Ton compte discord a été lié au profile NewbieContest suivant:', embed=NewbieExtension.build_profile_embed(origin.author.id, newbie_data[0], newbie_data[1], newbie_data[2]))

	@staticmethod
	async def unlink_newbie_account(origin: Message, args: list[str], cmd: Command):
		with NewbieExtension.new_session() as cursor:
			has_account = cursor.is_newbie_linked(d_id=origin.author.id)
		if not has_account:
			return await origin.reply('Ton compte discord n\'est pas lié à un profile NewbieContest!\nUtilise ``$ln <pseudo newbie>`` pour te connecter')

		with NewbieExtension.new_session() as cursor:
			cursor.unlink_newbie_user(origin.author.id)
		await origin.reply('Ton compte discord a été déconnecté de NewbieContest')

	@staticmethod
	async def show_leaderboard(origin: Message, args: list[str], cmd: Command):
		with NewbieExtension.new_session() as cursor:
			users = cursor.get_newbie_users()
		medals = {0: '🥇', 1: '🥈', 2: '🥉'}
		leaderboard_line = "%s ─ %s ─ [%s](%s) ─ %d (**%s**)\n"
		text = ""
		for pos, user in enumerate(users):
			text += leaderboard_line % (
				medals[pos] if pos < 3 else '',
				user.d_name if origin.guild.get_member(user.d_id) is None else "<@%d>" % user.d_id,
				user.n_name,
				"https://www.newbiecontest.org/index.php?page=info_membre&id=%d" % user.n_id,
				user.n_pts,
				NewbieExtension.rank_to_kingdom(user.n_pos)
			)

		embed = Embed()
		embed.set_author(name="Classement NewbieContest - %s" % origin.guild.name, icon_url=NewbieExtension.avatar_url)
		embed.description = text
		embed.set_footer(text="Dernière mise à jour")
		embed.timestamp = NewbieExtension.last_update
		embed.colour = int("0xFF0000", 16)

		await origin.reply(embed=embed)

	@staticmethod
	@tasks.loop(minutes=600)
	async def refresh_all():
		with NewbieExtension.new_session() as cursor:
			for newbieUser in cursor.get_newbie_users():
				_, n_pts, n_pos = await NewbieExtension.fetch_newbie_data(newbieUser.n_id)
				cursor.update_newbie_user(newbieUser.d_id, n_pts, n_pos)
				await sleep(0.1)
		NewbieExtension.last_update = datetime.now()

	@staticmethod
	def get_display_name() -> str:
		return "Newbie Integration"

	@staticmethod
	def get_short_name() -> str:
		return "newbie"

	@staticmethod
	def get_description() -> str:
		return "Lie ton compte NewbieContest et rejoint le classement local !"

	@staticmethod
	def get_author() -> str:
		return "Honeypot Hacker"

	@staticmethod
	def get_contributors() -> list[str]:
		return []

	@staticmethod
	def rank_to_kingdom(rank: int) -> str:
		ranks = {
			10: "1337",
			50: "hax0r",
			350: 'challenger',
			1650: 'script kiddy',
			20000: 'kikoo'
		}
		for lb, kd in ranks.items():
			if rank <= lb:
				return kd
		return "péon"

	@staticmethod
	def build_profile_embed(discord_id: int, username: str, points: int, position: int):
		embed = Embed()
		embed.set_author(name="Profile NewbieContest", icon_url=NewbieExtension.avatar_url)
		embed.add_field(name="Compte Discord", value="<@%d>" % discord_id)
		embed.add_field(name="Compte NewbieContest", value="%s" % username)
		embed.add_field(name="", value="")
		embed.add_field(name="Points", value=str(points))
		embed.add_field(name="Position", value=str(position))
		embed.add_field(name="Royaume", value=NewbieExtension.rank_to_kingdom(position))
		embed.colour = int("0xFF0000", 16)
		return embed

