from typing import Union
from discord import AllowedMentions, Client, Embed, Forbidden, Guild, Interaction, Message, Role, SelectOption, Member
from discord.utils import get
from discord.ui import View, Select, Button

from extensions import BaseExtension
from log import *


class RolesSelectionExtension(BaseExtension):

	allowed_mentions_obj = AllowedMentions(everyone=False, users=False, roles=False, replied_user=True)

	def __init__(self):
		super().__init__(
			display_name="Sélection de rôles",
			short_name="roles",
			description="Ajoute des messages de sélection de rôle pour les utilisateurs",
			author="Honeypot Hacker",
			contributors=[]
		)
		# Default settings
		self.register_extension_setting("admin_role", "-1")
		self.register_extension_setting("available_roles", {})
		self.register_extension_setting("roles_color", "CC2020")
		self.avatar_url = None

		if not self.is_configured():
			error("Settings for the RolesSelectionExtension are not properly configured")
		
	async def on_load(self, client: Client):
		await super().on_load(client)

		self.avatar_url = client.user.avatar.url

		await self.register_command(
			name="enablerole",
			description="Autorise un rôle à être choisi par les utilisateurs",
			aliases=["er"],
			usage="$er <role_id> <emoji> <description>",
			handler=self.add_available_role
		)
		await self.register_command(
			name="disablerole",
			description="Retire un rôle des choix possibles",
			aliases=["dr"],
			usage="$dr <role_id>",
			handler=self.rm_available_role
		)
		await self.register_command(
			name="listroles",
			description="Liste les rôles accessibles aux utilisateurs",
			aliases=["lr", "rolelist", "rl"],
			usage="$lr",
			handler=self.list_available_roles
		)
		await self.register_command(
			name="roles",
			description="Intéragit avec le message de sélection de rôles",
			aliases=["role", "r"],
			usage="$role",
			handler=self.role_message_interact
		)
	
	def is_configured(self):
		admin_role: str = self.get_extension_setting("admin_role", -1)
		if not admin_role.isnumeric() or int(admin_role) < 0:
			return False
		return True

	def is_authorized(self, origin: Message) -> bool:
		# TODO : A better permissions system should be added (hide unauthorized commands from help, reduce redundancy, etc.) but I'm too busy right now
		admin_role: str = self.get_extension_setting("admin_role")
		if not self.is_configured():
			error("Admin state cannot be verified as the configuration is not properly set")
			return False
		return get(origin.author.roles, id=int(admin_role)) is not None
	
	def is_role_enabled(self, r_id: int):
		roles = self.get_extension_setting("available_roles")
		return str(r_id) in roles

	async def _add_available_role(self, role_id: int, emoji: str, description: str):
		all_roles: dict = self.get_extension_setting("available_roles", {})
		all_roles[str(role_id)] = {'emoji': emoji, 'description': description}
		self.set_extension_setting("available_roles", all_roles)

	async def _rm_available_role(self, role_id: int):
		if self.is_role_enabled(role_id):
			all_roles: dict = self.get_extension_setting("available_roles", {})
			all_roles.pop(str(role_id))
			self.set_extension_setting("available_roles", all_roles)
	
	def get_roles(self, guild: Guild) -> list[tuple[Role, str, str]]:
		"""
		:return: List of tuples (Role instance, role emoji, role description)
		"""
		roles = []
		for r_id, r_desc in self.get_extension_setting("available_roles", {}).items():
			try:
				role = get(guild.roles, id=int(r_id))
			except:
				continue
			if role is not None:
				roles.append((role, r_desc['emoji'], r_desc['description']))
		return roles

	async def add_available_role(self, origin: Message, args: list[str]):
		if not self.is_authorized(origin):
			await origin.reply("Tu n'as pas le droit d'utiliser cette commande !")
			return
		
		if len(args) < 3 or not args[0].isnumeric() or len(args[1]) > 1:
			await self.help(origin, "enablerole")
			return
		
		# Retrieve role id
		r_id = int(args[0])
		try:
			role = get(origin.guild.roles, id=r_id)
		except:
			role = None
		if role is None:
			await origin.reply(f"Râté, il n'y a pas de rôle avec l'id ``{r_id}`` sur ce serveur.")
			return
		
		emoji = args[1]
		description = " ".join(args[2:])
		await self._add_available_role(r_id, emoji, description)

		await origin.reply(f"✅ Le rôle {role.mention} est maintenant autorisé.", allowed_mentions=self.allowed_mentions_obj)

	async def rm_available_role(self, origin: Message, args: list[str]):
		if not self.is_authorized(origin):
			await origin.reply("Tu n'as pas le droit d'utiliser cette commande !")
			return

		if len(args) != 1 or not args[0].isnumeric():
			await self.help(origin, "disablerole")
		
		await self._rm_available_role(int(args[0]))

		try:
			role = get(origin.guild.roles, id=int(args[0]))
		except:
			role = None

		await origin.reply(f"✅ Le rôle {role.mention if role is not None else args[0]} a été désactivé !", allowed_mentions=self.allowed_mentions_obj)
		
	async def list_available_roles(self, origin: Message, args: list[str]):
		if not self.is_authorized(origin):
			await origin.reply("Tu n'as pas le droit d'utiliser cette commande !")
			return

		roles = [f"> {r[1]} {r[0].mention} : {r[2]}" for r in self.get_roles(origin.guild)]

		if len(roles) == 0:
			await origin.reply("Aucun rôle n'est activé sur ce serveur.")
		else:
			await origin.reply(f"### Rôles activés ({len(roles)}):\n\t" + "\n\t".join(roles), allowed_mentions=self.allowed_mentions_obj)

	async def role_message_interact(self, origin: Message, args: list[str]):
		await origin.reply(embed=self._create_roles_embed(), view=RolePickView(self, origin.author))

	def _create_roles_embed(self) -> Embed:
		embed = Embed()
		embed.title = "Liste des rôles:"
		embed.set_author(name="HoneyPot Hacker - Roles", icon_url=self.avatar_url)
		embed.color = int(self.get_extension_setting('roles_color'), 16)
		embed.description = "\n".join(["%s <@&%s> > **%s**" % (r_desc['emoji'], r_id, r_desc['description']) for r_id, r_desc in self.get_extension_setting("available_roles", {}).items()])
		return embed
	

class RolePickSelect(Select):

	def __init__(self, ext: RolesSelectionExtension, roles, **kwargs):
		self.ext = ext
		self.roles = roles
		super().__init__(**kwargs)
	
	async def on_select_handler(self, author):
		added, removed, skipped = [], [], []
		for i in range(len(self.roles)):
			role = self.roles[i][0]
			if not self.ext.is_role_enabled(role.id):
				skipped.append(role)
				continue
			
			try:
				if str(i) in self.values:  # Role was picked
					if get(author.roles, id=role.id) is None:
						await author.add_roles(role)
						added.append(role)
				else:
					if get(author.roles, id=role.id) is not None:
						await author.remove_roles(role)
						removed.append(role)
			except Forbidden:
				skipped.append(role)
				
		return added, removed, skipped
	
	async def callback(self, interaction: Interaction):
		added, removed, skipped = await self.on_select_handler(interaction.user)
		
		if len(added) == 0 and len(removed) == 0 and len(skipped) == 0:  # No changes
			await interaction.response.defer()
			return
		
		msg = ""
		if len(added) != 0:
			msg += "Rôles ajoutés: " + ", ".join(r.mention for r in added) + "\n"
		if len(removed) != 0:
			msg += "Rôles supprimées: " + ", ".join(r.mention for r in removed) + "\n"
		if len(skipped) != 0:
			msg += "Rôles Ignorés: " + ", ".join(r.mention for r in skipped) + "\n"
		await interaction.response.send_message(
			msg,
			allowed_mentions=self.ext.allowed_mentions_obj,
			ephemeral=True,
			delete_after=10
		)

		await interaction.message.edit(embed=self.ext._create_roles_embed(), view=RolePickView(self.ext, interaction.guild.get_member(interaction.user.id)))
		

class RolePickView(View):

	def __init__(self, ext: RolesSelectionExtension, author: Member):
		self.ext = ext
		self.author_id = author.id
		super().__init__(timeout=120)
		
		roles = ext.get_roles(author.guild)
		if len(roles) > 25:
			error("More than 25 selectable roles. Please fix that with multiple selects")
			roles = roles[:25]

		options = [
			SelectOption(label=f"{roles[i][1]} {roles[i][0].name}", default=get(author.roles, id=roles[i][0].id) is not None, value=i)
			for i in range(len(roles))
		]

		self.add_item(RolePickSelect(ext, roles=roles, options=options, min_values=0, max_values=len(roles), placeholder="--- Aucun rôle sélectionné"))
		
	async def interaction_check(self, interaction):
		return interaction.user.id == self.author_id