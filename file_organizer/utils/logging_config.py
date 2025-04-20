"""Logging configuration for the file organizer."""

import logging
from datetime import datetime
from pathlib import Path


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Setup logging for the file organizer application.
    Creates a logs directory with timestamped log files.

    Args:
        verbose: Whether to enable verbose logging

    Returns:
        logging.Logger: Configured logger
    """
    # Create a logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create a timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"file_organizer_{timestamp}.log"

    # Configure logging
    level = logging.DEBUG if verbose else logging.INFO

    # Configure logger
    logger = logging.getLogger("file_organizer")
    logger.setLevel(level)

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # Create handlers
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()

    # Set format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.debug(f"Logging initialized. Log file: {log_file}")

    return logger
