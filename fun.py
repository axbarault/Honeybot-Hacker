import re
import discord
from discord.ext import commands
import random


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['bonjour', 'hello', 'salut', 'slt', 'yo', 'wesh', 'wait', 'what', 'cpt', 'message', 'wtf', 'allo'])
    async def motd(self, context):
        messages = ["Salutations !", "Hello !", "Wesh wesh", "Yo", "Bien ou bien ?", "Привет!", "Guten tag!", "你好！", "すみません、私はリンゴです",
                         "Yu-Gi-Oh!", "Déso fréro, mais la terre n'est pas plate", "Hier j'ai mangé une croustiflette, c'était incroyable, et c'était au Crous",
                         "La vie n'est qu'une patatoïde…", "Rien ne vaut le papier-crayon…", "Je sers pas à grand chose pour l'instant :(", "Cicéron, c'est pas carré",
                         "Le RSA n'est pas seulement une prestation sociale", "Life is not so papier-crayon :(", "Je pourrais faire des CTFs en vrai",
                         "N'oubliez pas, il est encore temps d'hacker Titouan Lux !", "Un truc que je pourrais faire aussi c'est de fournir des fonctions de chiffrage et de déchiffrage…",
                         "Askip je suis sur GitHub >:D", "Jz?c!njt Quesryu ?cci hplcdn y«;ddnf", "T3VpLCBqZSBtJ2VubnV5YWlz",
                         "Y'a pas que des memes là dedans mais tout n'est pas pertinent", "Il est possible que je me sois trompé de disposition de clavier à un moment",
                         "\"Il estoit, dit l’Estoile, homme tres-docte, mais vicieux\"", "Chocolatine… franchement…", "Quand la terreur de Belle Beille frappera-t-elle à nouveau ?", 
                         "Hackerman !", "Je rêve d'une banque…", "*\"Il\"* est pertinent à sa place…", "Improvise. Adapt. Overcome.", "J'adore l'eau",
                         "Pourquoi les pizzas rondes viennent-elles dans des boîtes carrées ?", "À quelle vitesse les petits pains se vendent-ils ?",
                         "Pourquoi se fait-il que lorsqu'on demande aux gens ce qu'ils apporteraient sur une île déserte, ils ne répondent jamais «un bateau» ?",
                         "Les personnes avec un bégaiement bégayent-elles aussi dans leurs pensées ?", "Pourquoi «séparé» s’écrit-il tout ensemble alors que «tout ensemble» s’écrit séparé ?"
                         "Un aveugle qui prédit l’avenir, est-ce qu’on appelle ça un voyant non-voyant ?",
                         "Si un astronaute commet un crime dans l’espace, est-ce que c’est un crime sans gravité ?", "Si tu manges des Pépitos après minuit, est-ce tu manges des Pépitards ?"]
        rnd = random.randint(0, len(messages)-1)
        reponse = messages[rnd]
        await context.reply(reponse)

    async def chocolatine(message): # yaayay
        words = re.split('\s+|\'|"', message.content)
        for word in words:
            if word.endswith("tine"):
                await message.reply("Sans te contredire %s, on ne dit pas %s mais pain au %s !" % (message.author.display_name, word, word[:-3]))
