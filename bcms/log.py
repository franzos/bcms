import logging
import sys
from logging.handlers import SysLogHandler, RotatingFileHandler

from .config import LOG_FILE_PATH, LOG_NAME

# Define a custom log level for console output
CONSOLE_LOG_LEVEL = logging.INFO

# Configure the logger
log = logging.getLogger(LOG_NAME)
log.setLevel(logging.DEBUG)

# Create a formatter for all log handlers
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
)

# Create a console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(CONSOLE_LOG_LEVEL)
ch.setFormatter(formatter)
log.addHandler(ch)

# Check the operating system
opsys = sys.platform.lower()

if opsys == "linux" or opsys.startswith("linux"):  # Handle different Linux variations
    # On Linux, log all events to file
    log_file_path = LOG_FILE_PATH
    fh = RotatingFileHandler(log_file_path, maxBytes=10000, backupCount=1)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # On Linux, engage syslog for warning-level and above logs
    sh = SysLogHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    log.addHandler(sh)
