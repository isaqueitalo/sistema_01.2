from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = BASE_DIR / "config.json"


@dataclass(slots=True)
class Config:
    app_name: str
    database_path: Path
    log_path: Path
    backup_dir: Path
    debug: bool
    theme: str
    default_admin: Dict[str, Any]
    company: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        database = (BASE_DIR / data.get("database_path", "DATA/system.db")).resolve()
        log_file = (BASE_DIR / data.get("log_path", "DATA/system.log")).resolve()
        backup_dir = (BASE_DIR / data.get("backup_dir", "BACKUP")).resolve()
        backup_dir.mkdir(parents=True, exist_ok=True)
        database.parent.mkdir(parents=True, exist_ok=True)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        return cls(
            app_name=data.get("app_name", "Sistema PDV"),
            database_path=database,
            log_path=log_file,
            backup_dir=backup_dir,
            debug=bool(data.get("debug", False)),
            theme=data.get("theme", "dark"),
            default_admin=data.get(
                "default_admin",
                {"username": "admin", "password": "admin123", "role": "admin"},
            ),
            company=data.get(
                "company",
                {
                    "name": "Loja",
                    "cnpj": "",
                    "address": "",
                    "phone": "",
                    "logo": "",
                },
            ),
        )


_config: Optional[Config] = None


def load_config(path: Optional[Path] = None) -> Config:
    """Load configuration from disk just once."""
    global _config
    if _config is None or path:
        cfg_path = path or CONFIG_FILE
        with cfg_path.open("r", encoding="utf-8-sig") as cfg_file:
            data = json.load(cfg_file)
        _config = Config.from_dict(data)
    return _config


def get_config() -> Config:
    return load_config()


__all__ = ["Config", "get_config", "load_config", "BASE_DIR"]
