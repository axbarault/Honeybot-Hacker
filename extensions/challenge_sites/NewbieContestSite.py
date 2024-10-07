import re
from asyncio import AbstractEventLoop

from extensions.challenge_sites.ChallengeSite import ChallengeSite
from settings import SQliteSession
from structures import NewbieUser


class NewbieContestSite(ChallengeSite[NewbieUser]):

	def __init__(self, scheduler: AbstractEventLoop):
		super().__init__(
			site_name="Newbie Contest",
			aliases=["newbie", "nc", "newbiecontest"],
			avatar_url="https://www.newbiecontest.org/images/logo.png",
			site_fns=SQliteSession.NEWBIE_FUNCTION_SET,
			display_name="Newbie Integration",
			short_name="newbie",
			scheduler=scheduler
		)

	def new_user_structure(self, **kwargs) -> NewbieUser:
		return NewbieUser(**kwargs)

	def get_user_url(self, user: NewbieUser) -> str:
		assert user.rm_id is not None
		return "https://www.newbiecontest.org/index.php?page=info_membre&id=%d" % user.rm_id

	def get_failed_fetch_message(self, attempt: str) -> str:
		return f"Il semblerait qu'aucun compte NewbieContest ne corresponde au pseudo __**{attempt}**__..."

	def get_leaderboard_complement(self, user: NewbieUser) -> str:
		return f"{user.rm_pts} (**{user.rm_kingdom}**)"

	async def fetch_user_data(self, into: NewbieUser):
		if into.rm_id is None and into.rm_name is None:
			return False

		if into.rm_id is None:
			# No user id was provided, we need to find it (Using the leaderboard and some bad regex)
			page = await self.request_webpage(f"https://www.newbiecontest.org/index.php?page=classementdynamique&member={into.rm_name}&nosmiley=1")
			if page.status_code != 200:
				return False
			# The following did not necessarily work when several matches were found
			# regex_result = re.findall(r"Recherche de.*id=(\d+)\">", page.text)
			regex_result = re.findall(rf"<a href=.*?;id=(\d+).*>\b{into.rm_name}\b", page.text, re.IGNORECASE)
			if len(regex_result) == 0:
				return False
			into.rm_id = int(regex_result[0])

		# Fetch the user profile page and use more bad regex to extract useful data
		page = await self.request_webpage(f"https://www.newbiecontest.org/index.php?page=info_membre&id=%d" % into.rm_id)
		name_regex = re.findall(r"Informations sur.*>\s*(.+?)(?:&nbsp|</span></a>)", page.text)
		pts_regex = re.findall(r"Points :.*>\s*(\d+)", page.text)
		pos_regex = re.findall(r"Position :.*>\s*(\d+)", page.text)

		if len(name_regex) == 0 or len(pts_regex) == 0:
			return False

		into.rm_name, into.rm_pts = name_regex[0], int(pts_regex[0])
		into.rm_pos = int(pos_regex[0]) if len(pos_regex) > 0 else 0  # Position of 0 means Not Ranked
		return True
