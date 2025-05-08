import os
import logging
from logging.handlers import RotatingFileHandler

def initialize_app_logger(log_directory = "logs"):
    os.makedirs(log_directory, exist_ok=True)

    # Application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_handler = RotatingFileHandler(
        os.path.join(log_directory, "app.log"),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    app_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    app_logger.addHandler(app_handler)