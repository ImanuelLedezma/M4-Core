import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

LOG_FORMAT: str = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
LOG_DIR: str = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs"))
LOG_FILE: str = os.path.join(LOG_DIR, "bot.log")

_initialized: bool = False

def init(name: str = "m4-core") -> logging.Logger:
    global _initialized
    logger: logging.Logger = logging.getLogger(name)
    if not _initialized:
        logger.setLevel(logging.INFO)
        formatter: logging.Formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

        stdout_handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

        os.makedirs(LOG_DIR, exist_ok=True)
        file_handler: TimedRotatingFileHandler = TimedRotatingFileHandler(LOG_FILE, when="midnight", backupCount=7)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        _initialized = True
    return logger
