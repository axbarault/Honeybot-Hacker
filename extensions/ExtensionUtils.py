from asyncio import sleep, create_task

from settings import SQliteSession, SQliteProvider


def new_session() -> SQliteSession:
	"""
	Create a new connection to the SQlite database
	"""
	return SQliteProvider.get_instance().new_session()


async def delayed_execution(coroutine, delay):
	"""
	Asynchronously executes `coroutine` after `delay` seconds
	"""
	async def _():
		await sleep(delay)
		coroutine()

	create_task(_())
