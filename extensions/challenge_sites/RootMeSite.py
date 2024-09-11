import json
import re
from asyncio import AbstractEventLoop

from extensions.challenge_sites import ChallengeSite
from log import error
from settings import SQliteSession
from structures import RootMeUser


class RootMeSite(ChallengeSite[RootMeUser]):

	def __init__(self, api_key: str, scheduler: AbstractEventLoop):
		super().__init__(
			site_name="RootMe",
			aliases=["rootme", "rm"],
			avatar_url="https://shop.root-me.org/cdn/shop/files/image.png",
			site_fns=SQliteSession.ROOTME_FUNCTION_SET,
			site_color="0x111216",
			scheduler=scheduler
		)
		self.api_key = api_key

	def new_user_structure(self, **kwargs) -> RootMeUser:
		return RootMeUser(**kwargs)

	def get_user_url(self, user: RootMeUser) -> str:
		return "https://root-me.org/%s" % user.rm_name

	def get_failed_fetch_message(self, attempt: str) -> str:
		if attempt.isnumeric():
			return f"Huh, on dirait qu'aucun compte RootMe ne correspond à l'UID __**{attempt}**__..."
		return f"Huh, je n'ai pas pu trouver de compte RootMe __**{attempt}**__... Vérifie que le pseudo entré soit complet !"

	def get_leaderboard_complement(self, user: RootMeUser) -> str:
		return f" (**{user.rm_rank}**)"

	async def fetch_user_data(self, into: RootMeUser) -> bool:
		if into.rm_id is None:
			if into.rm_name is None:
				return False  # Should never happen
			# Sadly I don't think we can get the user ID from a username without dirty regex :(
			page = await self.request_webpage(self.get_user_url(into))
			if page.status_code != 200:
				return False
			# Extract the user id from the profile image name (Other sources can be found if that one fails in the future)
			# DOESN'T WORK WHEN THE USER DOESN'T HAVE A CUSTOM PROFILE IMAGE
			# id_search = re.findall(rf"IMG/logo/auton(\d+).png.*alt=\"\b{into.rm_name}\b\"", page.text, re.IGNORECASE)

			# Extract the user id from the leaderboard's link title (For some reason it's set to be the user ID, which is nice for us)
			id_search = re.findall(rf"<td><a href=\"\b{into.rm_name}\b.*title=\"(\d+)\">", page.text, re.IGNORECASE)
			if len(id_search) == 0:
				return False
			into.rm_id = int(id_search[0])

		# Nice API, no need for dirty regex, yaayay happy :)
		url = "https://api.www.root-me.org/auteurs/%d" % into.rm_id
		page = await self.request_webpage(url, cookies={'api_key': self.api_key})

		if page.status_code == 401:
			error("The provided RootMe API Key is not valid and returned a 401 Error")
		if page.status_code != 200:
			return False

		data = json.loads(page.text)
		if isinstance(data, list):
			return False

		into.rm_name, into.rm_pts, into.rm_pos, into.rm_rank, into.rm_challs = data["nom"], data["score"], data["position"], data["rang"], len(data["validations"])
		return True
