from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import get_config

LOGGER_NAME = "sistema_logger"
_logger: Optional[logging.Logger] = None


def configure_logger() -> logging.Logger:
    global _logger
    if _logger:
        return _logger

    cfg = get_config()
    log_path: Path = cfg.log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG if cfg.debug else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    _logger = logger
    logger.debug("Logger configurado. Arquivo: %s", log_path)
    return logger


def get_logger() -> logging.Logger:
    return configure_logger()


__all__ = ["get_logger", "configure_logger", "LOGGER_NAME"]
