import re
import time
from random import randint

from discord import Message
from discord.ext.commands import Bot

import log
from command import Command
from extensions import BaseExtension, UtilitiesExtension


class FunExtension(BaseExtension):

	MAX_BOTTLE_LENGTH = 512

	async def on_load(self, client: Bot):
		self.register_command(
			name="motd",
			description="Y a qu'en essayant que tu comprendras",
			aliases=['bonjour', 'hello', 'salut', 'slt', 'yo', 'wesh', 'wait', 'what', 'cpt', 'message', 'wtf', 'allo'],
			usage=None,
			handler=FunExtension.motd
		)
		self.register_command(
			name="chocolatine",
			description="On est pas du sud nous",
			aliases=[],
			usage="$chocolatine <message>",
			handler=FunExtension.chocolatine
		)
		# Bouteille a la mer
		self.register_command(
			name="capsule",
			description="Ouvre ou envoie une bouteille à la mer",
			aliases=['bouteille'],
			usage="$capsule\n$capsule [message]",
			handler=FunExtension.capsule
		)
		self.register_extension_setting('capsule.format.open', '***{user}*** *casse la bouteille et lis le message glissé à l\'intérieur:*\n> \"{msg}\" - **{author}**\n*Une date est inscrite en bas de la page: *<t:{date}>')
		self.register_extension_setting('capsule.format.empty', '***{user}*** *casse une bouteille mais celle-ci était vide.*')
		self.register_extension_setting('capsule.format.too_long', '***{user}*** *écrit son message mais celui-ci est trop grand et ne rentre pas sur sa feuille. Notre protagoniste recommence.*')
		self.register_extension_setting('capsule.format.write', '***{user}*** *glisse un message dans une bouteille et la lance à la mer.*')
		self.register_extension_setting('capsule.format.overwrite', '***{user}*** *ignore le message dans la bouteille et place sa propre lettre à l\'intérieur.*')
		self.register_extension_setting('capsule.message', 'Si vous lisez ceci, c\'est que je suis mort...')
		self.register_extension_setting('capsule.author', client.user.display_name)
		self.register_extension_setting('capsule.date', int(time.time()))

	@staticmethod
	def get_display_name() -> str:
		return "Fun"

	@staticmethod
	def get_short_name() -> str:
		return "fun"

	@staticmethod
	def get_description() -> str:
		return "Ajoute une pincée de bonheur et une marmite de wtf"

	@staticmethod
	def get_author() -> str:
		return "Honeypot Hacker"

	@staticmethod
	def get_contributors() -> list[str]:
		return []

	@staticmethod
	async def motd(origin: Message, _: list[str], __: Command):
		messages = [
			"Salutations !", "Hello !", "Wesh wesh", "Yo", "Bien ou bien ?", "Привет!", "Guten tag!", "你好！",
			"すみません、私はリンゴです",
			"Yu-Gi-Oh!", "Déso fréro, mais la terre n'est pas plate",
			"Hier j'ai mangé une croustiflette, c'était incroyable, et c'était au Crous",
			"La vie n'est qu'une patatoïde…", "Rien ne vaut le papier-crayon…",
			"Je sers pas à grand chose pour l'instant :(", "Cicéron, c'est pas carré",
			"Le RSA n'est pas seulement une prestation sociale", "Life is not so papier-crayon :(",
			"Je pourrais faire des CTFs en vrai",
			"N'oubliez pas, il est encore temps d'hacker Titouan Lux !",
			"Un truc que je pourrais faire aussi c'est de fournir des fonctions de chiffrage et de déchiffrage…",
			"Askip je suis sur GitHub >:D", "Jz?c!njt Quesryu ?cci hplcdn y«;ddnf", "T3VpLCBqZSBtJ2VubnV5YWlz",
			"Y'a pas que des memes là dedans mais tout n'est pas pertinent",
			"Il est possible que je me sois trompé de disposition de clavier à un moment",
			"\"Il estoit, dit l’Estoile, homme tres-docte, mais vicieux\"", "Chocolatine… franchement…",
			"Quand la terreur de Belle Beille frappera-t-elle à nouveau ?",
			"Hackerman !", "Je rêve d'une banque…", "*\"Il\"* est pertinent à sa place…",
			"Improvise. Adapt. Overcome.", "J'adore l'eau",
			"Pourquoi les pizzas rondes viennent-elles dans des boîtes carrées ?",
			"À quelle vitesse les petits pains se vendent-ils ?",
			"Pourquoi se fait-il que lorsqu'on demande aux gens ce qu'ils apporteraient sur une île déserte, ils ne répondent jamais «un bateau» ?",
			"Les personnes avec un bégaiement bégayent-elles aussi dans leurs pensées ?",
			"Pourquoi «séparé» s’écrit-il tout ensemble alors que «tout ensemble» s’écrit séparé ?"
			"Un aveugle qui prédit l’avenir, est-ce qu’on appelle ça un voyant non-voyant ?",
			"Si un astronaute commet un crime dans l’espace, est-ce que c’est un crime sans gravité ?",
			"Si tu manges des Pépitos après minuit, est-ce tu manges des Pépitards ?"
		]
		rnd = randint(0, len(messages) - 1)
		await origin.reply(messages[rnd])

	@staticmethod
	async def chocolatine(origin: Message, args: list[str], self: Command):  # yaayay
		if origin.reference is not None:
			# Replying to a message, in which case we take that message's content as arguments
			target = await origin.channel.fetch_message(origin.reference.message_id)
			args = re.split("[\"\' ]+", target.content)
		else:
			# Not replying to a message
			if len(args) == 0:
				return await UtilitiesExtension.help_command(origin, [self.get_name()], self)
			target = origin

		# Count "tine" occurrences
		count = 0
		for word in args:
			if re.match("^.*tines?$", word):
				is_plural = word.endswith('s')
				await target.reply("Sans te contredire %s, on ne dit pas **%s** mais **pain%s au %s** !" % (origin.author.display_name, word, 's' if is_plural else '', word[:-4] if is_plural else word[:-3]))
				count += 1

		# If zero occurrence and someone was trying to PAIN AU CHOCOLAT someone else, make fun of them
		if count == 0 and target != origin:
			await origin.reply("Eh bé petit t'es pompette? Y a tchi d'mal dans ce qu'il a dit!")

	@staticmethod
	async def capsule(origin: Message, args: list[str], self: Command):
		if args.__len__() == 0:
			# Open the capsule
			capsule_cnt = FunExtension.get_extension_setting('capsule.message')
			capsule_author = FunExtension.get_extension_setting('capsule.author')
			capsule_date = FunExtension.get_extension_setting('capsule.date')

			if capsule_cnt is None:
				response: str = FunExtension.get_extension_setting('capsule.format.empty')
			else:
				response: str = FunExtension.get_extension_setting('capsule.format.open')

				FunExtension.set_extension_setting('capsule.message', None)
				FunExtension.set_extension_setting('capsule.author', None)
				FunExtension.set_extension_setting('capsule.date', None)

			await origin.reply(response.format(
				user=origin.author.display_name,
				msg=capsule_cnt,
				author=capsule_author,
				date=capsule_date
			))
		else:
			capsule_cnt = " ".join(args)
			capsule_author = origin.author.display_name

			await origin.delete()

			if capsule_cnt.__len__() > FunExtension.MAX_BOTTLE_LENGTH:
				response = FunExtension.get_extension_setting('capsule.format.too_long')
			else:
				if FunExtension.get_extension_setting('capsule.message') is None:
					response = FunExtension.get_extension_setting('capsule.format.write')
				else:
					response = FunExtension.get_extension_setting('capsule.format.overwrite')

				FunExtension.set_extension_setting('capsule.message', capsule_cnt)
				FunExtension.set_extension_setting('capsule.author', capsule_author)
				FunExtension.set_extension_setting('capsule.date', int(time.time()))

				log.info("New Bottled Message. Content: '{}'  |  Author : '{}'".format(capsule_cnt, origin.author.name))

			await origin.channel.send(response.format(user=capsule_author))
