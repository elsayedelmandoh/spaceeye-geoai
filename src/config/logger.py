"""
propose: configure logging to file and console for the project.
input: settings.PROJECT_NAME (logger name), settings.LOGS_DIR (log file path).
output: logs/PROJECT_NAME.log on disk, stdout stream in terminal.
"""

import logging
import sys

from src.config.config import settings

settings.create_required_directories()
LOG_FILE_PATH = settings.BASE_DIR / settings.LOGS_DIR / f"{settings.PROJECT_NAME}.log"
LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] -> %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(settings.PROJECT_NAME)
