import json
import logging.config
import os
import getpass
import pkg_resources


LOG_NAME = "bcms"

CONFIG = pkg_resources.resource_filename(__name__, "logging.json")
with open(CONFIG, "r", encoding="utf-8") as f:
    config = json.load(f)

logging.config.dictConfig(config)


def set_nonroot_logging():
    """Set the logging file to a non-root user location."""
    if getpass.getuser() != "root":
        # Create paths
        LOG_FILE_DIR = os.path.expanduser(f"~/.local/share/{LOG_NAME}")
        LOG_FILE_PATH = f"{LOG_FILE_DIR}/{LOG_NAME}.log"
        if not os.path.exists(LOG_FILE_DIR):
            os.makedirs(LOG_FILE_DIR)

        # Get the root logger
        root_logger = logging.getLogger()

        # Find the file handler
        file_handler = None
        for handler in root_logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                file_handler = handler
                break

        if file_handler:
            # Close the old file handler
            file_handler.close()
            root_logger.removeHandler(file_handler)

            # Create a new file handler with the updated filename
            new_file_handler = logging.handlers.RotatingFileHandler(LOG_FILE_PATH)
            new_file_handler.setLevel(file_handler.level)
            new_file_handler.setFormatter(file_handler.formatter)

            # Add the new file handler to the root logger
            root_logger.addHandler(new_file_handler)


def set_debugging(log):
    """Set the logging level to DEBUG for the root logger and all its handlers."""
    root_log = logging.getLogger()
    root_log.setLevel(logging.DEBUG)
    for handler in root_log.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.DEBUG)
    log.debug("Debug mode enabled ... really.")
