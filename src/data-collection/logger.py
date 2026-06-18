# Logger module for the scripts

import logging
import os
from logging.handlers import RotatingFileHandler

# Location for the log file
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "malditectist_v2.log")

# Create the logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Logging function
# Returns a configed logger with both terminal & rotating log file.
def get_logger(name: str) -> logging.Logger:

    # Create a log
    logger = logging.getLogger(name)
    
    # To avoid duplicate handlers if get_logger is called multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Logging formtat - timestamp, log level, module name, message
    formatter = logging.Formatter(
        fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Terminal handler (StreamHandler) - only logs INFO and above to terminal
    terminal_handler = logging.StreamHandler()
    terminal_handler.setLevel(logging.INFO)
    terminal_handler.setFormatter(formatter)
    
    # File handler 
    # logs DEBUG and above to file, rotates at 5MB and keeps 3 backups
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(terminal_handler)
    logger.addHandler(file_handler)

    return logger