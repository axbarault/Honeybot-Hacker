from datetime import datetime


class LogColors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'


def get_date_header():
	return "[%s]" % datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(log_type: str, message: str, color: str = ""):
	print("{}{} [{: <8}] {}{}".format(color, get_date_header(), log_type, message, LogColors.ENDC))


def warn(message):
	log("WARNING", message, LogColors.WARNING)


def info(message):
	log("INFO", message)


def debug(message):
	log("DEBUG", message, LogColors.OKCYAN)


def error(message):
	log("ERROR", message, LogColors.FAIL)
