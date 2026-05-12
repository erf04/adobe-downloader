import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name, log_file=None, level=logging.INFO, console=True):
    """Setup logger with console and file handlers"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter with more details
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler (if log_file provided)
    if log_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create a function to get loggers for different components
def get_downloader_logger():
    return setup_logger(
        'AdobeDownloader',
        'logs/downloader.log',
        level=logging.DEBUG
    )

def get_ffmpeg_logger():
    return setup_logger(
        'AdobeFFmpeg',
        'logs/ffmpeg.log',
        level=logging.DEBUG
    )

def get_main_logger():
    return setup_logger(
        'Main',
        'logs/main.log',
        level=logging.INFO
    )