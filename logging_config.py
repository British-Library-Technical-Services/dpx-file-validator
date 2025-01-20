import os
import logging
from datetime import datetime

def setup_logger():
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