import argparse
import discord
import discord.ext.commands


from os.path import abspath

from settings import SettingsStore, SQliteProvider
from command import CommandMap
from extensions import *
from log import *


parser = argparse.ArgumentParser( prog="Honeybot-Hacker", description="Start an instance of the Honeybot Discord Bot", epilog="Contributions are welcome ! Made with ♥ by the Honeypot Angers Team" )
parser.add_argument("-c", "--config", type=str, help="The configuration file to start from. Defaults to ./resources/config.json.", default="./resources/config.json")
args = parser.parse_args()

active_extensions = [
	VerificationExtension,
	UtilitiesExtension,
	SiteLeaderboardsExtension,
	FunExtension,
	RolesSelectionExtension
]

if __name__ == "__main__":
	rel_cfg_path = args.config
	settings = SettingsStore(abspath(rel_cfg_path))
	settings.set_default("prefix", "$")
	settings.set_default("discord-token", "*****")

	database = SQliteProvider('resources/members.db')

	intents = discord.Intents.all()
	prefix = settings.get('prefix')
	bot = discord.ext.commands.Bot(command_prefix=prefix, intents=intents)

	@bot.event
	async def on_ready():
		await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=prefix + "help"))
		info('Logged in as {0} ({0.id})'.format(bot.user))
		await load_extensions()

	@bot.event
	async def on_message(message: discord.Message):
		if message.author.id == bot.user.id or message.author.bot:
			return
		args = message.content.split(" ")
		if args[0].startswith(prefix):
			command_name = args.pop(0)[1:]
			if CommandMap.get_instance().command_exists(command_name):
				await CommandMap.get_instance().get_command(command_name).execute(message, args)

	async def load_extensions():
		BaseExtension.scheduler = bot.loop
		for c in active_extensions:
			ext = c()
			ExtensionStore.get_instance().register_extension(ext)
			await ext.on_load(bot)
	try:
		bot.run(settings.get('discord-token'))
	except discord.errors.LoginFailure:
		print("----------------------------")
		print("Invalid discord token provided ! It can be changed at " + abspath(rel_cfg_path))
		print("----------------------------")
