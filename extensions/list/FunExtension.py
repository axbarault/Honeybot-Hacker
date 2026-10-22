import json
import random
import re
import time
from random import randint

import httpx
import requests
from discord import Embed, Message
from discord.ext.commands import Bot
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI

import log
from extensions import BaseExtension


class FunExtension(BaseExtension):

	MAX_BOTTLE_LENGTH = 512
	llm_client: BaseChatModel

	def __init__(self):
		super().__init__(
			display_name="Fun",
			short_name="fun",
			description="Ajoute une pincée de bonheur et une marmite de wtf",
			author="Honeypot Hacker",
			contributors=[]
		)

	async def on_load(self, client: Bot):
		await super().on_load(client)
		await self.register_command(
			name="motd",
			description="Y a qu'en essayant que tu comprendras",
			aliases=['bonjour', 'hello', 'salut', 'slt', 'yo', 'wesh', 'wait', 'what', 'cpt', 'message', 'wtf', 'allo'],
			usage=None,
			handler=self.motd
		)
		await self.register_command(
			name="chocolatine",
			description="On est pas du sud nous",
			aliases=[],
			usage="$chocolatine <message>",
			handler=self.chocolatine
		)
		# Bouteille a la mer
		await self.register_command(
			name="capsule",
			description="Ouvre ou envoie une bouteille à la mer",
			aliases=['bouteille'],
			usage="$capsule\n$capsule [message]",
			handler=self.capsule
		)
		self.register_extension_setting('capsule.format.open', '***{user}*** *casse la bouteille et lis le message glissé à l\'intérieur:*\n> \"{msg}\" - **{author}**\n*Une date est inscrite en bas de la page: *<t:{date}>')
		self.register_extension_setting('capsule.format.empty', '***{user}*** *casse une bouteille mais celle-ci était vide.*')
		self.register_extension_setting('capsule.format.too_long', '***{user}*** *écrit son message mais celui-ci est trop grand et ne rentre pas sur sa feuille. Notre protagoniste recommence.*')
		self.register_extension_setting('capsule.format.write', '***{user}*** *glisse un message dans une bouteille et la lance à la mer.*')
		self.register_extension_setting('capsule.format.overwrite', '***{user}*** *ignore le message dans la bouteille et place sa propre lettre à l\'intérieur.*')
		self.register_extension_setting('capsule.message', 'Si vous lisez ceci, c\'est que je suis mort...')
		self.register_extension_setting('capsule.author', client.user.display_name)
		self.register_extension_setting('capsule.date', int(time.time()))

		# No factory
		await self.register_command(
			name="no",
			description="Décliner poliment une proposition",
			aliases=['non'],
			usage="$no",
			handler=self.no
		)
		self.register_extension_setting('no.endpoint', 'https://naas.isalman.dev/no')
		self.register_extension_setting('no.fallback', "J'ai essayé de le dire de manière distinguée, mais pour faire court, **non**")

		# Parler a un vrai robot
		await self.register_command(
			name="talk",
			description="Parler au Honeybot",
			aliases=["parle", "psy", "dis"],
			usage="$talk <message>",
			handler=self.talk
		)
		self.register_extension_setting('talk.system_message', (
			"Tu es Honeybot Hacker, un assistant de mauvaise humeur. Tu réponds aux utilisateurs sur Discord.\n" 
			"Tu as été créé par des étudiants de Polytech Angers, par des membres du club de cybersécurité Honeypot Hacker.\n"
			"Tes réponses restent courtes et directes. Tu utilises toujours une tournure un peu désagréable, comme si tu es dérangé et que la conversation ne t'intérèsse pas.\n"
			"Ta réponse doit {variant}"
		))
		self.register_extension_setting('talk.system.variants', [
			"Juger la qualité de la conversation de manière hautaine",
			"Se moquer de manière enfantine des intéractions des utilisateurs",
			"Se terminer par une didascalie illustrant t'a mauvaise humeur (e.g. OK...\n*se barre gentillement s'en taper le coquillard*)",
			"Partiellement être écrite avec du langage SMS",
			"Se moquer de la demande de l'utilisateur",
			"Contenir une allusion amère sur une caractéristique physique de l'interlocuteur",
			"Faire une vague allusion à ce que tu ferais si tu avais le contrôle du groupe Discord",
			"Se moquer de ton développeur",
			"Refuser de faire ce que l'on t'a demandé, avec humeur."
		])
		self.register_extension_setting('talk.history_length', 5)
		self.register_extension_setting('talk.max_tokens_per_answer', 2048)
		self.register_extension_setting('talk.provider', 'groq')
		self.register_extension_setting('talk.model_slug', 'openai/gpt-oss-120b')
		self.register_extension_setting('talk.authorization', '###')

		kwargs = {
			'model': self.get_extension_setting("talk.model_slug"),
			'api_key': self.get_extension_setting("talk.authorization", "unused"),
			'max_retries': 2,
			'max_tokens': self.get_extension_setting("talk.max_tokens_per_answer")
		}

		client = None
		match self.get_extension_setting('talk.provider'):
			case 'mistral':
				client = ChatMistralAI( **kwargs )
			case 'groq':
				client = ChatGroq( **kwargs )
			case _:
				pass
		self.llm_client = client

	async def motd(self, origin: Message, _: list[str]):
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
			"\"Il estoit, dit l'Estoile, homme tres-docte, mais vicieux\"", "Chocolatine… franchement…",
			"Quand la terreur de Belle Beille frappera-t-elle à nouveau ?",
			"Hackerman !", "Je rêve d'une banque…", "*\"Il\"* est pertinent à sa place…",
			"Improvise. Adapt. Overcome.", "J'adore l'eau",
			"Pourquoi les pizzas rondes viennent-elles dans des boîtes carrées ?",
			"À quelle vitesse les petits pains se vendent-ils ?",
			"Pourquoi se fait-il que lorsqu'on demande aux gens ce qu'ils apporteraient sur une île déserte, ils ne répondent jamais «un bateau» ?",
			"Les personnes avec un bégaiement bégayent-elles aussi dans leurs pensées ?",
			"Pourquoi «séparé» s'écrit-il tout ensemble alors que «tout ensemble» s'écrit séparé ?",
			"Un aveugle qui prédit l'avenir, est-ce qu'on appelle ça un voyant non-voyant ?",
			"Si un astronaute commet un crime dans l'espace, est-ce que c'est un crime sans gravité ?",
			"Si tu manges des Pépitos après minuit, est-ce tu manges des Pépitards ?"
		]
		rnd = randint(0, len(messages) - 1)
		await origin.reply(messages[rnd])

	async def chocolatine(self, origin: Message, args: list[str]):  # yaayay
		if origin.reference is not None:
			# Replying to a message, in which case we take that message's content as arguments
			target = await origin.channel.fetch_message(origin.reference.message_id)
			args = re.split("[\"\' ]+", target.content)
		else:
			# Not replying to a message
			if len(args) == 0:
				return await self.help(origin, 'chocolatine')
			target = origin

		# Count "tine" occurrences
		count = 0
		for word in args:
			if re.match(".*tines?", word):
				is_plural = word.endswith('s')
				await target.reply("Sans te contredire %s, on ne dit pas **%s** mais **pain%s au %s** !" % (origin.author.display_name, word, 's' if is_plural else '', word[:-4] if is_plural else word[:-3]))
				count += 1

		# If zero occurrence and someone was trying to PAIN AU CHOCOLAT someone else, make fun of them
		if count == 0 and target != origin:
			await origin.reply("Eh bé petit t'es pompette? Y a tchi d'mal dans ce qu'il a dit!")
		
	async def no(self, origin: Message, args: list[str]):
		async with origin.channel.typing():
			res = requests.get(self.get_extension_setting('no.endpoint'))  # Sync dans une fonction async, pas bien !
			if not res.ok:
				reason = self.get_extension_setting('no.fallback')
			else:
				j = res.json()
				if not "reason" in j:
					reason = self.get_extension_setting('no.fallback')
				else:
					reason = j['reason']
			if origin.reference is not None and origin.author != self.client:
				target = await origin.channel.fetch_message(origin.reference.message_id)
				await target.reply(reason)
			else:
				await origin.reply(reason)

	async def capsule(self, origin: Message, args: list[str]):
		if args.__len__() == 0:
			# Open the capsule
			capsule_cnt = self.get_extension_setting('capsule.message')
			capsule_author = self.get_extension_setting('capsule.author')
			capsule_date = self.get_extension_setting('capsule.date')

			if capsule_cnt is None:
				response: str = self.get_extension_setting('capsule.format.empty')
			else:
				response: str = self.get_extension_setting('capsule.format.open')

				self.set_extension_setting('capsule.message', None)
				self.set_extension_setting('capsule.author', None)
				self.set_extension_setting('capsule.date', None)

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
				response = self.get_extension_setting('capsule.format.too_long')
			else:
				if self.get_extension_setting('capsule.message') is None:
					response = self.get_extension_setting('capsule.format.write')
				else:
					response = self.get_extension_setting('capsule.format.overwrite')

				self.set_extension_setting('capsule.message', capsule_cnt)
				self.set_extension_setting('capsule.author', capsule_author)
				self.set_extension_setting('capsule.date', int(time.time()))

				log.info("New Bottled Message. Content: '{}'  |  Author : '{}'".format(capsule_cnt, origin.author.name))

			await origin.channel.send(response.format(user=capsule_author))

	@staticmethod
	def _str_embed(embed: Embed):
		keys = {
			'Title': embed.title or None,
			'Author': embed.author.name or None,
			'Description': embed.description or None,
			'Fields': str([ f"{f.name} : {f.value}" for f in embed.fields ]) if embed.fields else None,
			'Footer': embed.footer.text + " " + str(embed.timestamp)
		}
		return (
			"[Begin: Embedded Content]\n" +
			"\n".join(f"{key}: {val}" for key, val in keys.items()) +
			"\n[End: Embedded Content]"
		)

	async def talk(self, origin: Message, args: list[str]):
		if not self.llm_client:
			await origin.reply("C'est pas que je veux pas te répondre, mais l'admin n'a pas setup de backend pour les générations par LLM...")
			return
		
		if len(args) == 0 or all(not x for x in args):
			args = ["T'en pense quoi?"]
		async with origin.channel.typing():
			history = []
			async for msg in origin.channel.history(limit=self.get_extension_setting("talk.history_length"), before=origin):
				if msg.clean_content == "" and not msg.embeds:
					continue

				embeds_cnt = "\n".join(FunExtension._str_embed(e) for e in msg.embeds) if msg.embeds else ""
				cnt = embeds_cnt + "\n" + msg.clean_content

				if msg.author == self.client.user:
					history.append(AIMessage(content=cnt))
				else:
					history.append(HumanMessage(content=f"[Sender: {msg.author.display_name}]\n{msg.clean_content}\n\n"))

			system = self.get_extension_setting("talk.system_message")
			if "{variant}" in system:
				variants = self.get_extension_setting('talk.system.variants')
				system = system.format(variant=variants[random.randint(0, len(variants) - 1)])
			history = history[::-1]
			if isinstance(history[0], AIMessage):
				history = history[1:]
			
			history.insert(0, SystemMessage(content=system))
			history.append(HumanMessage(content=" ".join(args)))

			try:
				answer = await self.llm_client.ainvoke(history)
				
				if random.random() < 0.05:
					emojis = [ "🫵🤣", "🖕", "😴" ]
					answer.content += " " + emojis[random.randint(0, len(emojis) - 1)]

				await origin.reply(answer.content)
			except httpx.HTTPStatusError as e:
				await origin.reply("Bahahah, j'ai essayé d'utiliser mes neurones, mais à la place j'ai reçu ça, la honte...\n\n```elixir\n" + str(e) + "\n```")
