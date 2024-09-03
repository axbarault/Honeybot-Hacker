from typing import Any

from discord.ui import View, Button
from discord.errors import NotFound, Forbidden
from discord.utils import get
from discord.ext.commands import Bot
from discord import TextChannel, Role, Embed, ButtonStyle, ComponentType, Interaction, Message, Member

from extensions import SqlExtension
from log import *


class VerificationExtension(SqlExtension):

	avatar_url: str = None
	verif_msg: Message = None
	verif_channel: TextChannel = None
	verif_role: Role = None

	async def on_load(self, client: Bot):
		VerificationExtension.avatar_url = client.user.avatar.url
		client.add_listener(self.on_member_join)
		self.set_default_config()
		await self.setup_verification_channel(client)

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

	async def setup_verification_channel(self, client: Bot):
		if not await self.parse_channel_and_role(client):  # Error occurred while parsing
			return

		# Build the embed
		embed = Embed()
		embed.set_author(name=self.get_extension_setting('rules_title'), icon_url=VerificationExtension.avatar_url)
		embed.colour = int(self.get_extension_setting('rules_color'), 16)
		embed.description = self.get_extension_setting('rules_content')
		embed.set_footer(text=self.get_extension_setting('rules_footer'))
		embed.timestamp = datetime.now()

		if not await self.clear_verif_channel(client):  # Channel didn't need to be cleared, edit the last message
			await self.verif_msg.edit(embed=embed, view=VerifyMessageView())
		else:  # Channel was cleared, send a new message
			await self.verif_channel.send(embed=embed, view=VerifyMessageView())

	async def parse_channel_and_role(self, client: Bot):
		"""
		Parse both the verification channel and the verified role
		:param client: Bot user
		:return: True if both could be parsed, false on error
		"""
		verif_channel_id: str = str(self.get_extension_setting('channel', '-1'))
		verif_role_id: str = str(self.get_extension_setting('role', '-1'))

		has_error = False
		if not verif_channel_id.isnumeric() or int(verif_channel_id) < 0:
			error("Veuillez entrer dans la configuration un identifiant de canal textuel valide (Actuel : %s)" % verif_channel_id)
			has_error = True
		if not verif_role_id.isnumeric() or int(verif_role_id) < 0:
			error("Veuillez entrer dans la configuration un identifiant de rôle de vérification valide (Actuel : %s)" % verif_role_id)
			has_error = True
		if has_error:
			return False

		try:
			VerificationExtension.verif_channel = await client.fetch_channel(int(verif_channel_id))
			if not isinstance(VerificationExtension.verif_channel, TextChannel):
				error("Le channel de vérification (ID: %s) n'est pas un salon textuel" % verif_channel_id)
				return False
			VerificationExtension.verif_role = get(VerificationExtension.verif_channel.guild.roles, id=int(verif_role_id))
		except NotFound:
			error("Le channel de vérification (ID: %s) n'existe pas ou n'est pas visible par le bot. Veuillez le modifier dans le fichier de configuration" % verif_channel_id)
			return False

		if VerificationExtension.verif_role is None:
			error("Le rôle de vérification (ID: %s) n'existe pas. Veuillez le modifier dans le fichier de configuration" % verif_role_id)
			return False

		return True

	async def clear_verif_channel(self, client: Bot) -> bool:
		"""
		Clear the channel if it isn't cleared already (If the last message is not one sent by the bot)
		:param client: Bot user (Used to check the last author id)
		:return: True if the channel was cleared, False otherwise
		"""
		#
		if VerificationExtension.verif_channel.last_message_id is None:
			return False
		VerificationExtension.verif_msg = await self.verif_channel.fetch_message(self.verif_channel.last_message_id)
		if VerificationExtension.verif_msg.author.id != client.user.id:
			await VerificationExtension.verif_channel.purge(limit=100)
			return True
		return False

	async def on_member_join(self, member: Member):
		channel = member.guild.system_channel
		message: str = self.get_extension_setting('welcome_message')
		fields = {
			'{mention}': member.mention,
			'{server}': member.guild.name,
			'{channel}': self.verif_channel.mention,
			'{username}': member.display_name
		}
		for k, v in fields.items():
			message = message.replace(k, v)
		await channel.send(message)

	@staticmethod
	def get_display_name() -> str:
		return "Vérification"

	@staticmethod
	def get_short_name() -> str:
		return "verification"

	@staticmethod
	def get_description() -> str:
		return "Demande aux nouveaux utilisateurs de se vérifier en intéragissant avec un message"

	@staticmethod
	def get_author() -> str:
		return "Honeypot Hacker"

	@staticmethod
	def get_contributors() -> list[str]:
		return []

	def setup_tables(self) -> None:
		with self.new_session() as cursor:
			cursor.create_discord_users_table()


class VerifyUserButton(Button):

	async def callback(self, interaction: Interaction) -> Any:
		"""
		Called when a user interacts with the button
		"""
		# Check if the user already exists
		has_role = get(interaction.user.roles, id=VerificationExtension.verif_role.id) is not None
		with VerificationExtension.new_session() as cursor:
			if cursor.is_verified(interaction.user.id):
				msg_id = 'rules_accept.on_verify' if not has_role else 'rules_accept.on_reverify'
			else:
				msg_id = 'rules_accept.on_verify'
				cursor.verify(interaction.user.id, interaction.user.display_name)

		if not has_role:
			try:
				await interaction.user.add_roles(VerificationExtension.verif_role, reason="Rules accepted")
			except Forbidden:
				msg_id = 'rules_accept.on_error'
				error("Missing permissions to verify user %s" % interaction.user.display_name)

		await interaction.response.send_message(VerificationExtension.get_extension_setting(msg_id), ephemeral=True, delete_after=10)


class VerifyMessageView(View):

	def __init__(self):
		super().__init__(timeout=None)
		self.add_item(VerifyUserButton(
			style=ButtonStyle.success,
			custom_id='verify_user',
			label=VerificationExtension.get_extension_setting('rules_accept.text'),
			emoji=VerificationExtension.get_extension_setting('rules_accept.emoji'),
		))
