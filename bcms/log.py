import logging
import sys
import os
import getpass
from logging.handlers import SysLogHandler, RotatingFileHandler

from .config import LOG_NAME

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

LOG_FILE_PATH = f"/var/log/{LOG_NAME}.log"
if getpass.getuser() != "root":
    LOG_FILE_DIR = os.path.expanduser(f"~/.local/share/{LOG_NAME}")
    LOG_FILE_PATH = f"{LOG_FILE_DIR}/{LOG_NAME}.log"
    if not os.path.exists(LOG_FILE_DIR):
        os.makedirs(LOG_FILE_DIR)


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
