import os
import logging
from logging import Formatter, handlers
from .colors import Colors

__all__ = ["setup_logging"]

LEVEL_COLORS = {
	logging.DEBUG: Colors.blue.value,
	logging.INFO: Colors.white.value,
	logging.WARNING: Colors.yellow.value,
	logging.ERROR: Colors.red.value,
	logging.CRITICAL: Colors.red_bold.value,
}

DATE_COLOR = Colors.grey.value
RESET_COLOR = Colors.default.value
MESSAGE_COLOR = Colors.default.value

class StyledFormatter(Formatter):
	"""
	Der StyledFormatter erweitert den Standard-Formatter von Python, um farbige Log-Ausgaben in der Konsole zu ermöglichen. 
	Er überschreibt die format-Methode, um die verschiedenen Teile der Log-Nachricht (Zeitstempel, Log-Level, Logger-Name und Nachricht) mit den definierten Farben zu versehen. 
	Die Farben werden basierend auf dem Log-Level ausgewählt, um eine bessere visuelle Unterscheidung der Log-Nachrichten zu ermöglichen.
	"""
	def format(self, record: logging.LogRecord) -> str:
		"""
		Formatiert die Log-Nachricht mit den entsprechenden Farben für Zeitstempel, Log-Level, Logger-Name und Nachricht.

		:param record: Das LogRecord-Objekt, das die Informationen über die Log-Nachricht enthält.
		:type record: logging.LogRecord
		:return: Die formatierte Log-Nachricht als String.
		:rtype: str
		"""
		level_color = LEVEL_COLORS.get(record.levelno, Colors.white.value)
		formatted = super().format(record)

		time_str = self.formatTime(record, self.datefmt)
		colored_time = f"{DATE_COLOR}{time_str}{RESET_COLOR}"
		formatted = formatted.replace(time_str, colored_time, 1)

		colored_levelname = f"{level_color}{record.levelname}{RESET_COLOR}"
		formatted = formatted.replace(record.levelname, colored_levelname, 1)

		colored_name = f"{Colors.magenta.value}{record.name}{RESET_COLOR}"
		formatted = formatted.replace(record.name, colored_name, 1)

		message_str = record.getMessage()
		colored_message = f"{MESSAGE_COLOR}{message_str}{RESET_COLOR}"
		formatted = formatted.replace(message_str, colored_message, 1)

		return formatted

logger = logging.getLogger()    

def setup_logging(level: int = logging.INFO, log_folder: str= "./logs", log_file: str ="app.log", mb:int=5, backup_count: int = 5):
	"""
	Richtet das Logging für die Anwendung ein.

	:param level: Das Log-Level, das verwendet werden soll.
	:type level: int
	:param log_folder: Der Ordner, in dem die Log-Dateien gespeichert werden sollen.
	:type log_folder: str
	:param log_file: Der Name der Log-Datei.
	:type log_file: str
	:param mb: Die maximale Größe der Log-Datei in Megabyte.
	:type mb: int
	:param backup_count: Die Anzahl der Backup-Dateien, die aufbewahrt werden sollen.
	:type backup_count: int
	"""
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


