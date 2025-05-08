import os
import logging
from logging.handlers import RotatingFileHandler

def initialize_audit_logger(log_directory = "logs"):
    os.makedirs(log_directory, exist_ok=True)
    
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_handler = RotatingFileHandler(
        os.path.join(log_directory, "audit.log"),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    audit_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(message)s'
    ))
    audit_logger.addHandler(audit_handler)