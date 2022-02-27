import discord
from discord.utils import get
from discord.ext import commands

from config import config
from sqlite import sqlite as db


class Members(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.slash_command(name="refreshmembers", description="Rafraichir la liste des membres")
    @commands.command(name="refreshmembers", aliases=['f5'])
    @commands.has_permissions(manage_guild=True)
    async def refreshMembersList(self, context):
        members = context.guild.members
        for member in members:
            db.addUser(member.id)
        await context.send("La liste des membres a été mise à jour dans la base de donnnées")

    @refreshMembersList.error
    async def refreshMembersList_error(self, context, error):
        if(isinstance(error, commands.MissingPermissions)):
            await context.send("Vous n'avez pas la permission d'éxécuter cette commande !")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if config.rulesMessageId == payload.message_id and config.rulesChannelId == payload.channel_id and payload.emoji.name == '✅':
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            member_role = get(guild.roles, name="hacker")
            await member.add_roles(member_role)
            db.updateRules(payload.user_id, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if config.rulesMessageId == payload.message_id and config.rulesChannelId == payload.channel_id and payload.emoji.name == '✅':
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            member_role = get(guild.roles, name="hacker")
            await member.remove_roles(member_role)
            db.updateRules(payload.user_id, False)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        system_channel = guild.system_channel
        if system_channel:
            rules_channel = guild.get_channel(config.rulesChannelId)
            await system_channel.send("Bienvenue à %s chez **%s** ! Va accepter les règles ici -> %s" % (member.mention, guild.name, rules_channel.mention))
        db.addUser(member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # db.removeUser(member.id)
        pass
