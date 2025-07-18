import logging
import os
from datetime import datetime

def setup_logging():
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(logging.INFO)

    log_dir = 'log'
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_filename = os.path.join(log_dir, f"download_log_{timestamp}.txt")

    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)