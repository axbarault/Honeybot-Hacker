from asyncio import create_task, sleep

from settings import SQliteProvider, SQliteSession


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
