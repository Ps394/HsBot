
import logging
from logging import Formatter, handlers
import os

COLORS = {
	"CYAN": "\033[36m",
	"CYANBOLD": "\033[1;36m",
	"RED": "\033[31m",
	"REDBOLD": "\033[1;31m",
	"ORANGE": "\033[38;5;208m",
	"ORANGEBOLD": "\033[1;38;5;208m",
	"GREEN": "\033[32m",
	"YELLOW": "\033[33m",
	"YELLOWBOLD": "\033[1;33m",
	"BLUE": "\033[34m",
	"BLUEBOLD": "\033[1;34m",
	"MAGENTA": "\033[35m",
	"MAGENTABOLD": "\033[1;35m",
	"WHITE": "\033[37m",
	"WHITEBOLD": "\033[1;37m",
	"SILVER": "\033[90m",
	"SILVERBOLD": "\033[1;90m",
	"GREY": "\033[30m",
	"GREYBOLD": "\033[1;30m",
}

LEVEL_COLORS = {
	logging.DEBUG: COLORS["BLUE"],
	logging.INFO: COLORS["BLUE"],
	logging.WARNING: COLORS["ORANGE"],
	logging.ERROR: COLORS["RED"],
	logging.CRITICAL: COLORS["REDBOLD"],
}

DATE_COLOR = COLORS["GREY"]
RESET_COLOR = "\033[0m"
MESSAGE_COLOR = COLORS["WHITE"]

class StyledFormatter(Formatter):
	def format(self, record: logging.LogRecord) -> str:
		level_color = LEVEL_COLORS.get(record.levelno, COLORS["WHITE"])
		formatted = super().format(record)

		time_str = self.formatTime(record, self.datefmt)
		colored_time = f"{DATE_COLOR}{time_str}{RESET_COLOR}"
		formatted = formatted.replace(time_str, colored_time, 1)

		colored_levelname = f"{level_color}{record.levelname}{RESET_COLOR}"
		formatted = formatted.replace(record.levelname, colored_levelname, 1)

		colored_name = f"{COLORS['MAGENTA']}{record.name}{RESET_COLOR}"
		formatted = formatted.replace(record.name, colored_name, 1)

		message_str = record.getMessage()
		colored_message = f"{MESSAGE_COLOR}{message_str}{RESET_COLOR}"
		formatted = formatted.replace(message_str, colored_message, 1)

		return formatted

logger = logging.getLogger()
logger.propagate = False
logging.getLogger("discord").propagate = False
logging.getLogger("aiosqlite").propagate = False
logging.getLogger("websockets").propagate = False
    

def setup_logging(level: int = logging.INFO, log_folder: str= "logs", log_file: str ="app.log", mb:int=5, backup_count: int = 5):
	mb = mb * 1024 * 1024
	os.mkdir(log_folder) if not os.path.exists(log_folder) else None
	global logger
	logger.setLevel(level)
	base_format = '{asctime} {levelname:<8} {name}: {message}'
	date_format = '%Y-%m-%d %H:%M:%S'

	file_handler = handlers.RotatingFileHandler(
		filename=os.path.join(log_folder, log_file),
		encoding='utf-8',
		maxBytes=mb,
		backupCount=backup_count
	)
	file_handler.setFormatter(Formatter(base_format, date_format, style='{'))
	
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(StyledFormatter(base_format, date_format, style='{'))
	
	logger.handlers.clear()
	logger.addHandler(file_handler)
	logger.addHandler(console_handler)


