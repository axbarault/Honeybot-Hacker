import os
import discord
from discord.ext import commands

from config import config
from help import Help
from fun import Fun

if __name__ == "__main__":

    bot = commands.Bot(command_prefix=lambda e, f: config.getPrefix(), help_command=None)

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=config.getPrefix()+"help"))
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')

    @bot.event
    async def on_message(message):
        if message.author.id == bot.user.id or message.author.bot:
            return
        
        await bot.process_commands(message)

    bot.add_cog(Help(bot))
    bot.add_cog(Fun(bot))

    bot.run(config.token)
