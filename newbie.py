import discord
from discord.ext import commands, tasks

import re
import requests
from time import time, ctime
from asyncio import sleep
from sqlite import sqlite as db
from newbieUser import NewbieUser
from help import Help

class Newbie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lastDBUpdate = time()
        self.printer.start()

    async def readNewbieUser(self, id):
        if id.isdecimal():
            id = int(id)
        else:
            r = await self.bot.loop.run_in_executor(None, lambda: requests.get("https://www.newbiecontest.org/index.php?page=classementdynamique&member=%s&nosmiley=1" % id))

            p_id = re.compile("Recherche de.*id=(\d+)")
            try:
                id = int(p_id.findall(r.text)[0])
            except:
                raise Exception("Compte NewbieContest %s introuvable" % id)

        r = await self.bot.loop.run_in_executor(None, lambda: requests.get("https://www.newbiecontest.org/index.php?page=info_membre&id=%d" % id))

        p_login = re.compile("Informations sur.*>\s*(.+)</span></a>")
        p_points = re.compile("Points :.*>\s*(\d+)")
        p_kingdom = re.compile("Royaume :.*>\s*([\w\s]+)\s*</p>")
        p_position = re.compile("Position :.*>\s*(\d+)")
        try:
            login = p_login.findall(r.text)[0]
            points = int(p_points.findall(r.text)[0])
            position = int(p_position.findall(r.text)[0])
        except:
            raise Exception("Compte NewbieContest %d introuvable" % id)

        return id, login, points, position

    # @commands.slash_command(name="linknewbie", description="Permet de lier son compte discord au compte newbiecontest")
    @commands.command(name='linknewbie', aliases=['ln', 'newbie'])
    async def link_newbie(self, context, login: str = None):
        if login is None:
            return await context.send(embed=Help.get("newbie", "ln"))

        try:
            id, login, points, position = await self.readNewbieUser(login)
        except Exception as e:
            return await context.send(str(e))

        newbieUser = NewbieUser(context.author.id, id, login, points, position)
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
        embed.set_footer(text="Dernière mise à jour : %s" % ctime(self.lastDBUpdate))

        await context.send(embed=embed)

    @tasks.loop(hours=24)
    async def printer(self):
        newbieUsers = db.getNewbieUsers()
        for newbieUser in newbieUsers:
            id, login, points, position = await self.readNewbieUser(str(newbieUser.id))
            newbieUser.login = login
            newbieUser.points = points
            newbieUser.position = position
            db.updateNewbie(newbieUser)
            await sleep(0.1)
        self.lastDBUpdate = time()

    @printer.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()