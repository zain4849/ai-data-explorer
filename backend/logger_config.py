import logging
import os
import uuid

from pythonjsonlogger import json as json_logger


def setup_logger():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    handler = logging.StreamHandler()

    if os.getenv("APP_ENV") == "production":
        formatter = json_logger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    else:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    handler.setFormatter(formatter)

    root = logging.getLogger("ai-data-explorer")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level, logging.INFO))
    return root


def generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


logger = setup_logger()
