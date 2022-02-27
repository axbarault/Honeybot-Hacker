import discord
from discord.ext import commands

import re
import requests
from sqlite import sqlite as db
from newbieUser import NewbieUser
from help import Help

class Newbie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.slash_command(name="linknewbie", description="Permet de lier son compte discord au compte newbiecontest")
    @commands.command(name='linknewbie', aliases=['ln', 'newbie'])
    async def link_newbie(self, context, login: str = None):
        if login is None:
            return await context.send(embed=Help.get("newbie", "ln"))

        self.id = login
        if isinstance(self.id, str):
            r = await self.bot.loop.run_in_executor(None, lambda: requests.get("https://www.newbiecontest.org/index.php?page=classementdynamique&member=%s&nosmiley=1" % self.id))

            p_id = re.compile("tCell tCellHL.*id=(\d+)")
            try:
                self.id = int(p_id.findall(r.text)[0])
            except:
                raise Exception("introuvable")

        r = await self.bot.loop.run_in_executor(None, lambda: requests.get("https://www.newbiecontest.org/index.php?page=info_membre&id=%d" % self.id))

        p_login = re.compile("Informations sur.*>\s*(\w+)")
        p_points = re.compile("Points :.*>\s*(\d+)")
        p_kingdom = re.compile("Royaume :.*>\s*([\w\s]+)\s*</p>")
        p_position = re.compile("Position :.*>\s*(\d+)\s*")
        try:
            self.login = p_login.findall(r.text)[0]
            self.points = int(p_points.findall(r.text)[0])
            self.position = int(p_position.findall(r.text)[0])
        except:
            raise Exception("introuvable")

        newbieUser = NewbieUser(context.author.id, self.id, self.login, self.points, self.position)
        db.updateNewbie(newbieUser)

        await context.send("Le compte Discord %s a été lié au compte NewbieContest %s !" % (context.author.mention, newbieUser.login))

    # @commands.slash_command(name="classement", description="Affiche le classement NewbieContest")
    @commands.command(name='classement', aliases=['rank', 'top', 'clas'])
    async def show_rank(self, context):
        guild = context.guild
        newbieUsers = db.getNewbieUsers()
        newbieUsers.sort(key=lambda newbieUser: newbieUser.points, reverse=True)

        medals = {1: '🥇', 2: '🥈', 3: '🥉'}

        text = ""
        pos = 0
        for newbieUser in newbieUsers:
            pos += 1
            text += "%s ─ %s ─ [%s](%s) ─ %d\n" % (str(pos) if pos > 3 else medals[pos],
                                                   guild.get_member(newbieUser.discord_id).mention,
                                                   newbieUser.login,
                                                   "https://www.newbiecontest.org/index.php?page=info_membre&id=%d" % newbieUser.id,
                                                   newbieUser.points)
            text += "\n"

        embed = discord.Embed(
            description=text,
            color=0xAA0000
        )
        embed.set_author(name="Classement NewbieContest de %s" % guild.name, icon_url="https://www.newbiecontest.org/images/logo.png")

        await context.send(embed=embed)
