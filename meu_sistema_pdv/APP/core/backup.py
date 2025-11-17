from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .config import get_config
from .logger import get_logger

logger = get_logger()


def criar_backup_manual() -> Path:
    cfg = get_config()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    destino = cfg.backup_dir / f"system_{timestamp}.db"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cfg.database_path, destino)
    logger.info("Backup criado em %s", destino)
    return destino


__all__ = ["criar_backup_manual"]
