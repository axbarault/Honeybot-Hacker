from discord import Message, Embed
from discord.ext.commands import Bot

from settings import SettingsStore
from command import CommandMap, Command
from extensions import BaseExtension, ExtensionStore


class UtilitiesExtension(BaseExtension):

	def __init__(self):
		super().__init__(
			display_name="Utilités",
			short_name="utilities",
			description="Implémente plein de commandes utiles",
			author="Honeypot Hacker",
			contributors=[]
		)
		self.avatar_url: str = ""
		# Default settings
		self.register_extension_setting('help.command_color', '0xBCBCBC')
		self.register_extension_setting('help.extension_color', '0xBCBC00')
		self.register_extension_setting('help.unknown_color', '0xBC0000')

	async def on_load(self, client: Bot):
		self.avatar_url = client.user.avatar.url
		# Commands
		await self.register_command(
			name="help",
			description="Affiche une page d'aide",
			aliases=["aide", "h", "oskour", "aled", "???"],
			usage="$help\n$help <commande>\n$help <extension>",
			handler=self.help_command
		)

	async def help_command(self, origin: Message, args: list[str]):
		embed = Embed()
		prefix = SettingsStore.get_instance().get('prefix')

		if len(args) == 0:
			# Show extensions help
			color = self.get_extension_setting('help.extension_color')
			embed.set_author(name="Honeybot - Extensions", icon_url=self.avatar_url)
			for extension in ExtensionStore.get_instance().get_extensions():
				embed.add_field(
					name = extension.display_name,
					value = "-> %shelp %s" % (prefix, extension.short_name)
				)
				embed.add_field(name="", value="")
				embed.add_field(
					name = "Description",
					value = extension.description
				)
		else:
			# Show specific help (Figure out whether we should display help for an extension or a command)
			args[0] = args[0].lower()
			if args[0].startswith(prefix):
				# The priority between command or extension help changes if there's the bot's prefix at the beginning of arg 0
				args[0] = args[0][1:]
				subject = CommandMap.get_instance().get_command(args[0]) or CommandMap.get_instance().get_command(args[0])
			else:
				subject = ExtensionStore.get_instance().get_extension(args[0]) or CommandMap.get_instance().get_command(args[0])

			if isinstance(subject, BaseExtension):
				color = self.get_extension_setting('help.extension_color')
				# Build the embed header (Presentation of the extension)
				embed.set_author(name="Extension - %s par %s" % (subject.display_name, subject.author), icon_url=self.avatar_url)
				embed.title = "Description de l'extension"
				embed.description = subject.description
				if len(subject.contributors) > 0:
					embed.add_field(
						name="Contributeur%s" % ("s" if len(subject.contributors) > 1 else ""),
						value=", ".join(subject.contributors),
						inline=False
					)
				# Build each command's help
				for command in subject.get_commands():
					has_usage = command.get_usage() is not None
					embed.add_field(
						name="%s%s" % (prefix, command.get_name()),
						value=command.get_description(),
						inline=has_usage
					)
					if has_usage:
						# Add a usage field
						embed.add_field(name="", value="")
						embed.add_field(
							name="Utilisation",
							value=command.get_usage()
						)
			elif isinstance(subject, Command):
				color = self.get_extension_setting('help.command_color')
				embed.set_author(name="Commande - %s%s du module %s" % (prefix, subject.get_name(), subject.get_extension()), icon_url=self.avatar_url)
				embed.add_field(name="Description", value=subject.get_description(), inline=False)
				if len(subject.get_aliases()) != 0:
					embed.add_field(name="Alias", value=", ".join(subject.get_aliases()), inline=False)
				if subject.get_usage() is not None:
					embed.add_field(name="Utilisation", value=subject.get_usage(), inline=False)
			else:
				color = self.get_extension_setting('help.unknown_color')
				embed.set_author(name="Commande ou extension inconnue", icon_url=self.avatar_url)
				embed.description = "Je n'ai pas trouvé d'extension nommée ``%s`` ou de commande ``%s%s``" % (args[0], prefix, args[0])
				embed.add_field(name="Liste des extensions", value="%shelp" % prefix, inline=False)
				embed.add_field(name="Détails d'une extension", value="%shelp <extension>" % prefix, inline=False)
				embed.add_field(name="Manuel d'une commande", value="%shelp %s<commande>" % (prefix, prefix), inline=False)

		embed.colour = int(color, 16)
		await origin.reply(embed=embed)
