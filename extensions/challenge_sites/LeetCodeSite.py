import json
from asyncio import AbstractEventLoop

import requests
from discord import Embed

from extensions.challenge_sites import ChallengeSite
from log import error
from settings import SQliteSession
from structures import LeetCodeUser


class LeetCodeSite(ChallengeSite[LeetCodeUser]):

	def __init__(self, api_key: str, scheduler: AbstractEventLoop):
		super().__init__(
			site_name="LeetCode",
			aliases=["lc", "leet", "leetcode"],
			avatar_url="https://upload.wikimedia.org/wikipedia/commons/8/8e/LeetCode_Logo_1.png",
			site_fns=SQliteSession.LEETCODE_FUNCTION_SET,
			site_color="0xffff64",
			scheduler=scheduler
		)
		# It actually seems the publicly available data doesn't require an API key
		self.api_key = api_key
		self.api_endpoint = "https://leetcode.com/graphql"
		self.api_headers = {
			'Content-Type': 'application/json',
			'Cookie': 'csrftoken=%s' % self.api_key,
			'Referer': 'https://leetcode.com/',
			'X-Csrftoken': self.api_key
		}

	def build_profile_embed(self, user: LeetCodeUser) -> Embed:
		embed = super().build_profile_embed(user)
		embed.set_thumbnail(url=user.rm_avatar)
		return embed

	def new_user_structure(self, **kwargs) -> LeetCodeUser:
		return LeetCodeUser(**kwargs)

	async def fetch_user_data(self, into: LeetCodeUser) -> bool:
		if into.rm_name is None:
			return False
		body = self.graphql_fetch_user.copy()
		body['variables'] = {'username': into.rm_name}
		page = await self.scheduler.run_in_executor(None, lambda: requests.post(self.api_endpoint, headers=self.api_headers, data=json.dumps(body)))

		if page.status_code != 200:
			if page.status_code == 401:
				error("The provided LeetCode API Key is not valid and returned a 401 Error")
			return False

		profile_data: dict = json.loads(page.text)

		if not isinstance(profile_data, dict) or len(profile_data.get('errors', [])) != 0:
			return False

		body = self.graphql_fetch_solves.copy()
		body['variables'] = {'username': into.rm_name}
		page = await self.scheduler.run_in_executor(None, lambda: requests.post(self.api_endpoint, headers=self.api_headers, data=json.dumps(body)))
		solve_stats: dict = json.loads(page.text)

		user_data = profile_data['data']['matchedUser']
		solves_data = solve_stats['data']['userProfileUserQuestionProgressV2']

		# Fill in the user structure
		into.rm_name, into.rm_pos, into.rm_avatar = user_data['username'], user_data['profile']['ranking'], user_data['profile']['userAvatar']
		into.rm_solved = [
			solves_data['numAcceptedQuestions'][0]['count'],
			solves_data['numAcceptedQuestions'][1]['count'],
			solves_data['numAcceptedQuestions'][2]['count']
		]

		return True

	async def link_account(self, user: LeetCodeUser) -> int:
		user.rm_id = user.rm_name
		return await super().link_account(user)

	def get_user_url(self, user: LeetCodeUser) -> str:
		return "https://leetcode.com/u/%s/" % user.rm_name

	def get_failed_fetch_message(self, attempt: str) -> str:
		return f"Hmm, je n'ai pas réussi à récupérer de compte LeetCode sous le pseudonyme __**{attempt}**__..."

	def get_leaderboard_complement(self, user: LeetCodeUser) -> str:
		return f"{user.rm_pos} (**{sum(user.rm_solved)} challenges**)"

	########################
	# GraphQL query bodies #
	########################

	graphql_fetch_user: dict = {
		'query': """
				query userPublicProfile($username: String!) {
					matchedUser(username: $username) {
						username
						profile {
							ranking
							userAvatar
						}
					}
				}
			""",
		'operationName': 'userPublicProfile'
	}
	graphql_fetch_solves: dict = {
		'query': """
				query userProfileUserQuestionProgressV2($username: String!) {
					userProfileUserQuestionProgressV2(userSlug: $username) {
						numAcceptedQuestions {
							count
						}
					}
				}
		""",
		'operationName': 'userProfileUserQuestionProgressV2'
	}
