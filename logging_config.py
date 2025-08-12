"""Logging configuration helper.

Provides a single `setup_logger` function that initialises the root logging
configuration for the validation service:
    * Creates a time‑stamped log file under a local `./logs` directory
    * Sets log level to INFO
    * Defines a concise format including timestamp, module, level, message

The log file name pattern: YYYY-MM-DD_HH-MM-SS_dpx_data.log
Console (stream) logging can be enabled by uncommenting the StreamHandler
line below if interactive visibility is desired alongside file capture.
"""

import os
import logging
from datetime import datetime

def setup_logger():
    """Initialise application-wide logging.

    Ensures the logs directory exists, builds a unique timestamped log file
    path, and configures the root logger with file handler output. Safe to
    call multiple times; subsequent calls to `basicConfig` will be ignored if
    logging has already been configured in this process.
    """
    log_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f"{timestamp}_dpx_data.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s:%(module)s:%(levelname)s:%(message)s',
        handlers=[
            logging.FileHandler(log_file),
            # logging.StreamHandler()
        ]
    )