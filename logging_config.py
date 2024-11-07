import os
import logging
from datetime import datetime

def setup_logger(location):
    if not os.path.exists(location):
        os.makedirs(location)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(location, f"{timestamp}_dpx_data.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s:%(module)s:%(levelname)s:%(message)s',
        handlers=[
            logging.FileHandler(log_file),
            # logging.StreamHandler()
        ]
    )