import discord
import os
from datetime import datetime
from discord.ext import commands
from config import config

categories = {
    'description': {
        'newbie': 'Commandes liées à NewbieContest (pour l\'instant rien ne marche, c\'est pour se donner une idée)',
        'autres': 'Autres commandes'
    },
    'displayName': {
        'newbie': 'NewbieContest',
        'autres': 'Autres'
    }
}

commandsList = {
    'description': {
        'newbie': {
            'nrank': 'Affiche son rang sur le newbie contest (pas implémenté)',
            'npseudo': 'Mets-à-jour le pseudo NC associé à ton compte discord (pas implémenté)',
        },
        'autres': {
            'bonjour': 'Hello !'
        }
    },
    'usage': {
        'newbie': {
            'npseudo': '<ton pseudo newbie contest>',
        },
        'autres': {
            
        }
    }
}


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get(context, category, command):
        PREFIX = config.getPrefix()
        title = "Commande %s%s" % (PREFIX, command)

        embed = discord.Embed(
            title = title,
            description = commandsList['description'][category][command],
            color = 0xDEDEDE
        )
        embed.set_author(
            name = "Aide",
            icon_url = ""
        )

        if command in commandsList['usage'][category]:
            embed.add_field(
                name = "Utilisation",
                value = "%s%s %s" % (PREFIX, command, commandsList['usage'][category][command]),
                inline = False
            )

        last_update = datetime.fromtimestamp(int(os.path.getmtime(os.path.realpath(__file__))))
        embed.set_footer(text="Dernière mise à jour : %s" % last_update)

        return embed

    @commands.command(aliases=['aide', 'h', 'oskour', 'aled'])
    async def help(self, context, query: str = None):
        PREFIX = config.getPrefix()
        embed = discord.Embed(
            color = 0xDEDEDE
        )
        last_update = datetime.fromtimestamp(int(os.path.getmtime(os.path.realpath(__file__))))
        embed.set_footer(text="Dernière mise à jour : %s" % last_update)

        if query is None:
            for category in categories['description']:
                embed.set_author(
                    name = "Aide de %s" % (self.bot.user.display_name),
                    icon_url = ""
                )
                embed.title = 'Liste des catégories de commandes'
                embed.add_field(
                    name = categories['displayName'][category],
                    value = "-> %shelp %s\n%s" % (PREFIX, category, categories['description'][category]),
                    inline = False
                )
        else:
            if query in categories['description']:
                category = query
                embed.set_author(
                    name = "Aide de %s" % (categories['displayName'][category]),
                    icon_url = ""
                )
                embed.title = 'Liste des commandes de %s' % categories['displayName'][category]
                for command in commandsList['description'][category]:
                    if command in commandsList['usage'][category]:
                        embed.add_field(
                            name = PREFIX+command,
                            value = commandsList['description'][category][command],
                            inline = True
                        )
                        embed.add_field(
                            name = "Utilisation",
                            value = "%s%s %s" % (PREFIX, command, commandsList['usage'][category][command]),
                            inline = True
                        )
                    else:
                        embed.add_field(
                            name = PREFIX+command,
                            value = commandsList['description'][category][command],
                            inline = False
                        )
            else:
                return await context.send("La catégorie %s n'existe pas\n%shelp pour obtenir de l'aide" % (query, PREFIX))

        return await context.send(embed=embed)
