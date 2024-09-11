from typing import Any, Union

import discord.errors
from discord.ui import View, Button
from discord.errors import NotFound, Forbidden
from discord.utils import get
from discord.ext.commands import Bot
from discord import TextChannel, Role, Embed, ButtonStyle, Interaction, Message, Member

from extensions import SqlExtension
from extensions.ExtensionUtils import new_session
from log import *


class VerificationExtension(SqlExtension):

	def __init__(self):
		super().__init__(
			display_name="Vérification",
			short_name="verification",
			description="Demande aux nouveaux utilisateurs de se vérifier en interagissant avec un message",
			author="Honeypot Hacker",
			contributors=[]
		)
		self.avatar_url = ""
		self.verif_msg: Union[Message, None] = None
		self.verif_channel: Union[TextChannel, None] = None
		self.verif_role: Union[Role, None] = None
		self.setup_tables()

	def is_extension_enabled(self) -> bool:
		return self.verif_channel is not None and self.verif_role is not None

	async def on_load(self, client: Bot):
		self.avatar_url = client.user.avatar.url
		# The listener is added because a welcome message is still sent in the case where the verif channel is set up but not the verif role
		client.add_listener(self.on_member_join)
		self.set_default_config()
		# Try to set up a verification channel. The extension won't work if the config isn't properly defined
		if not await self.setup_verification_channel(client) or self.verif_role is None:
			error("L'extension de Vérification des membres n'a pas pu être activée. Veuillez régler les erreurs ci-dessus et redémarrer le bot.")

	def set_default_config(self):
		self.register_extension_setting('channel', '-1')
		self.register_extension_setting('role', '-1')
		self.register_extension_setting('rules_title', 'Honeypot Hacker - Règles')
		self.register_extension_setting('rules_content', 'Ceci est un placeholder, il peut être changé dans le fichier de configuration du bot')
		self.register_extension_setting('rules_footer', 'Dernière mise à jour')
		self.register_extension_setting('rules_color', '0xFF0000')
		self.register_extension_setting('rules_accept.text', 'Accepter')
		self.register_extension_setting('rules_accept.emoji', '✅')
		self.register_extension_setting('rules_accept.on_verify', 'Merci d\'avoir accepté les règles! Tu as maintenant accès aux autres channels du serveur :wink:')
		self.register_extension_setting('rules_accept.on_reverify', 'Merci, mais tu as déjà accepté les règles! Va donc profiter de tous les autres channels du serveur :wink:')
		self.register_extension_setting('rules_accept.on_error', 'Woops, on dirait que je n\'ai pas les permissions pour te vérifier... Je préviens les admin, mais n\'hésite pas à les avertir également !')
		self.register_extension_setting('welcome_message', 'Bienvenue à {mention} chez {server}! Va accepter les règles ici -> {channel}')

	async def setup_verification_channel(self, client: Bot) -> bool:
		await self.parse_channel_and_role(client)
		if self.verif_channel is None:
			return False

		# Build the embed
		embed = Embed()
		embed.set_author(name=self.get_extension_setting('rules_title'), icon_url=self.avatar_url)
		embed.colour = int(self.get_extension_setting('rules_color'), 16)
		embed.description = self.get_extension_setting('rules_content')
		embed.set_footer(text=self.get_extension_setting('rules_footer'))
		embed.timestamp = datetime.now()

		if not await self.clear_verif_channel(client):  # Channel didn't need to be cleared, edit the last message
			await self.verif_msg.edit(embed=embed, view=VerifyMessageView(self))
		else:  # Channel was cleared, send a new message
			await self.verif_channel.send(embed=embed, view=VerifyMessageView(self))

		return True

	async def parse_channel_and_role(self, client: Bot):
		"""
		Try to parse both the verification channel and the verified role
		:param client: Bot user
		"""
		# Parse the config
		verif_channel_id: str = str(self.get_extension_setting('channel', '-1'))
		verif_role_id: str = str(self.get_extension_setting('role', '-1'))

		# Validate config data format
		has_error = False
		if not verif_channel_id.isnumeric() or int(verif_channel_id) < 0:
			error("Veuillez entrer dans la configuration un identifiant de canal textuel valide (Actuel : %s)" % verif_channel_id)
			has_error = True
		if not verif_role_id.isnumeric() or int(verif_role_id) < 0:
			error("Veuillez entrer dans la configuration un identifiant de rôle de vérification valide (Actuel : %s)" % verif_role_id)
			has_error = True
		if has_error:
			return

		# Try to match the channel id to a known channel
		try:
			self.verif_channel = await client.fetch_channel(int(verif_channel_id))
		except (NotFound, Forbidden):
			error("Le channel de vérification (ID: %s) n'existe pas ou n'est pas visible par le bot. Veuillez le modifier dans le fichier de configuration" % verif_channel_id)
			return

		# Error messages to pinpoint the channel problem if there is one
		if self.verif_channel is not None and not isinstance(self.verif_channel, TextChannel):
			error("Le channel de vérification (ID: %s) n'est pas un salon textuel" % verif_channel_id)
			return

		# There is no need to check that the verification channel is valid here because we've returned in every case where it wasn't
		# Try to match the role id to a known role
		self.verif_role = get(self.verif_channel.guild.roles, id=int(verif_role_id))
		if self.verif_role is None:
			error("Le rôle de vérification (ID: %s) n'existe pas. Veuillez le modifier dans le fichier de configuration" % verif_role_id)

	async def clear_verif_channel(self, client: Bot) -> bool:
		"""
		Clear the channel if it isn't cleared already (If the last message is not one sent by the bot)
		:param client: Bot user (Used to check the last author id)
		:return: True if the channel was cleared, False otherwise
		"""
		if self.verif_channel.last_message_id is None:
			return True

		try:
			self.verif_msg = await self.verif_channel.fetch_message(self.verif_channel.last_message_id)
		except discord.errors.NotFound:
			self.verif_msg = None
			return True

		if self.verif_msg.author.id != client.user.id:
			await self.verif_channel.purge(limit=100)
			return True
		return False

	async def on_member_join(self, member: Member):
		channel = member.guild.system_channel
		message: str = self.get_extension_setting('welcome_message')
		await channel.send(message.format(
			mention=member.mention,
			server=member.guild.name,
			channel=self.verif_channel.mention if self.verif_channel is not None else "``### ERROR ###``",
			username=member.display_name
		))

	def setup_tables(self) -> None:
		with new_session() as cursor:
			cursor.create_discord_users_table()


class VerifyUserButton(Button):

	def __init__(self, ext: VerificationExtension, **kwargs):
		self.ext = ext
		super().__init__(**kwargs)

	async def callback(self, interaction: Interaction) -> Any:
		"""
		Called when a user interacts with the button
		"""
		msg_id = 'rules_accept.on_error'
		if self.ext.verif_role is not None:
			# Check if the user already exists in the database
			has_role = get(interaction.user.roles, id=self.ext.verif_role.id) is not None
			with new_session() as cursor:
				if cursor.is_verified(interaction.user.id):
					# Greet them anyway even if they are already present in the database
					msg_id = 'rules_accept.on_verify' if not has_role else 'rules_accept.on_reverify'
				else:
					# Verify them in the database ONLY if they are not already present
					msg_id = 'rules_accept.on_verify'
					cursor.verify(interaction.user.id, interaction.user.display_name)

			if not has_role:
				try:
					await interaction.user.add_roles(self.ext.verif_role, reason="Rules accepted")
				except Forbidden:
					msg_id = 'rules_accept.on_error'
					error("Les permissions pour vérifier %s ne sont pas suffisamment élevées." % interaction.user.display_name)
				except NotFound:
					msg_id = 'rules_accept.on_error'
					error("Le role de vérification n'est plus accessible et %s n'a pas pu être vérifié." % interaction.user.display_name)
		else:
			error("%s n'a pas pu être vérifié car le role entré dans la config n'est pas valide." % interaction.user.display_name)

		await interaction.response.send_message(self.ext.get_extension_setting(msg_id), ephemeral=True, delete_after=20)


class VerifyMessageView(View):

	def __init__(self, ext: VerificationExtension):
		super().__init__(timeout=None)
		self.add_item(VerifyUserButton(
			ext,
			style=ButtonStyle.success,
			custom_id='verify_user',
			label=ext.get_extension_setting('rules_accept.text'),
			emoji=ext.get_extension_setting('rules_accept.emoji'),
		))
