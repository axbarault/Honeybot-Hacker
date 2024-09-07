import re
import requests

from typing import Union
from datetime import datetime
from asyncio import sleep

from discord import Message, Embed
from discord.ext import tasks
from discord.ext.commands import Bot

from extensions import SqlExtension
from log import error


class RootMeExtension(SqlExtension):

	def __init__(self):
		super().__init__(
			display_name="RootMe Integration",
			short_name="rootme",
			description="Lie ton compte RootMe à Discord et participe à la leaderboard du club !",
			author="Honeypot Hacker",
			contributors=[]
		)
		self.avatar_url = "https://shop.root-me.org/cdn/shop/files/image.png"
		self.last_update = datetime.now()

	def setup_tables(self) -> None:
		with self.new_session() as cursor:
			cursor.create_rootme_users_table()

	async def on_load(self, client: Bot):
		await self.register_command(
			name='linkrootme',
			description='Lie ton compte Discord à ton profile RootMe',
			aliases=['lrm'],
			usage='$lrm <pseudo rootme>',
			handler=self.link_rootme_account
		)
		await self.register_command(
			name='unlinkrootme',
			description='Déconnecte ton compte Discord de ton profile RootMe',
			aliases=['ulrm'],
			usage='$ulrm <pseudo rootme>',
			handler=self.unlink_rootme_account
		)
		await self.register_command(
			name='toprm',
			description='Affiche le classement RootMe du serveur',
			aliases=[],
			usage=None,
			handler=self.show_leaderboard
		)

		self.refresh_all.start()

	@tasks.loop(minutes=60)
	async def refresh_all(self):
		with self.new_session() as cursor:
			users = cursor.get_rootme_users()
		for rmUser in users:
			data = await self.fetch_user_data(rmUser.rm_name)
			if data is not None:
				_, rm_pos, rm_points, rm_challs = data
				with self.new_session() as cursor:
					cursor.update_rootme_user(rmUser.d_id, rm_pos, rm_points, rm_challs)
			else:
				error("Impossible de mettre à jour les données du profile RootMe %s : Profile inexistant" % rmUser.rm_name)
			await sleep(0.1)
		self.last_update = datetime.now()

	async def fetch_user_data(self, rm_name: str) -> Union[tuple[str, int, int, int], None]:
		url = f"https://www.root-me.org/{rm_name}?lang=fr"
		profile = await self.scheduler.run_in_executor(None, lambda: requests.get(url))

		# Check if the profile actually exists
		if profile.status_code != 200:
			return None

		profile = profile.text
		p_data = re.compile("\s/>&nbsp;(\d+)</h3>")
		user_data = p_data.findall(profile)
		if len(user_data) != 4:
			error("RootMe regex n'a pas retourné le bon nombre d'arguments (Attendu : 4, Reçu : %d)" % len(user_data))
			return None

		p_name = re.compile("profil de ([A-Za-z\d]+)\s\[Root Me")
		user_name = p_name.findall(profile)
		if len(user_name) == 0:
			error(f"RootMe regex n'a pas trouvé le nom d'utilisateur du profile {rm_name}. La casse entrée par l'utilisateur sera utilisée.")
		else:
			rm_name = user_name[0]

		return rm_name, int(user_data[0]), int(user_data[1]), int(user_data[2])

	async def link_rootme_account(self, origin: Message, args: list[str]):
		if len(args) == 0:
			return await self.help(origin, 'lrm')

		rm_name = " ".join(args)
		with self.new_session() as cursor:
			is_discord_linked = cursor.is_rootme_linked(d_id=origin.author.id)
			is_rm_linked = cursor.is_rootme_linked(rm_name=rm_name)

		if is_discord_linked:
			return await origin.reply('Ton compte discord est déjà lié à un profile RootMe!\nUtilise ``$ulrm`` pour te déconnecter et réessaye après')
		if is_rm_linked:
			return await origin.reply('Ce profile RootMe est déjà lié à un compte Discord!\nContact un admin si tu es le propriétaire de ce compte. Sinon, bien tenté, mais non ^^')

		rm_data = await self.fetch_user_data(rm_name)
		if rm_data is None:
			return await origin.reply(f'Aucun compte RootMe n\'est reconnu sous le pseudo **{rm_name}**')

		with self.new_session() as cursor:
			cursor.link_rootme_user(origin.author.id, rm_data[0], rm_data[1], rm_data[2], rm_data[3])
		await origin.reply('Ton compte discord a été lié au profile **RootMe** suivant:', embed=self.build_profile_embed(origin.author.id, rm_data[0], rm_data[1], rm_data[2], rm_data[3]))

	async def unlink_rootme_account(self, origin: Message, _: list[str]):
		with self.new_session() as cursor:
			has_account = cursor.is_rootme_linked(d_id=origin.author.id)
		if not has_account:
			return await origin.reply('Ton compte discord n\'est pas lié à un profile RootMe!\nUtilise ``$lrm <pseudo rootme>`` pour te connecter')

		with self.new_session() as cursor:
			cursor.unlink_rootme_user(origin.author.id)
		await origin.reply('Ton compte discord a été déconnecté de RootMe')

	async def show_leaderboard(self, origin: Message, _: list[str]):
		with self.new_session() as cursor:
			users = cursor.get_rootme_users()
		medals = {0: '🥇', 1: '🥈', 2: '🥉'}
		leaderboard_line = "%s ─ %s ─ [%s](%s) ─ %d points\n"
		text = ""
		for pos, user in enumerate(users):
			text += leaderboard_line % (
				medals[pos] if pos < 3 else f'#{pos + 1}',
				(user.d_name or user.rm_name) if origin.guild.get_member(user.d_id) is None else "<@%d>" % user.d_id,
				user.rm_name,
				"https://www.root-me.org/%s?lang=fr" % user.rm_name,
				user.rm_points
			)

		embed = Embed()
		embed.set_author(name="Classement RootMe - %s" % origin.guild.name, icon_url=self.avatar_url)
		embed.description = text
		embed.set_footer(text="Dernière mise à jour")
		embed.timestamp = self.last_update
		embed.colour = int("0x111216", 16)

		await origin.reply(embed=embed)

	def build_profile_embed(self, discord_id, rm_name, rm_pos, rm_points, rm_challs):
		embed = Embed()
		embed.set_author(name="Profile RootMe", icon_url=self.avatar_url)
		embed.add_field(name="Compte Discord", value="<@%d>" % discord_id)
		embed.add_field(name="Compte RootMe", value="%s" % rm_name)
		embed.add_field(name="", value="")
		embed.add_field(name="Points", value=str(rm_points))
		embed.add_field(name="Position", value=str(rm_pos) if rm_pos > 0 else "HC")
		embed.add_field(name="Challenges", value=str(rm_challs))
		embed.colour = int("0x111216", 16)
		return embed

