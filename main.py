
import logging
from HmWz import setup_logging


logger = logging.getLogger("Main")

setup_logging(log_file="bot.log", level=logging.INFO)

logger.debug("This is a debug message.")
logger.info("This is an info message.")
logger.warning("This is a warning message.")
logger.error("This is an error message.")
try:
    1 / 0
except ZeroDivisionError:
    logger.critical("An exception occurred", exc_info=True)
