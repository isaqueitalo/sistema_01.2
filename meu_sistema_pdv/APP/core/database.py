from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, Optional

from .config import get_config
from .logger import get_logger

logger = get_logger()
_thread_local = threading.local()


def _connect() -> sqlite3.Connection:
    cfg = get_config()
    db_path: Path = cfg.database_path
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_connection() -> sqlite3.Connection:
    conn = getattr(_thread_local, "connection", None)
    if conn is None:
        conn = _connect()
        _thread_local.connection = conn
    return conn


@contextmanager
def db_cursor(commit: bool = False) -> Generator[sqlite3.Cursor, None, None]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Erro em operação com o banco de dados")
        raise
    finally:
        cursor.close()


def execute(
    query: str,
    params: Iterable[Any] | Dict[str, Any] | None = None,
    *,
    fetchone: bool = False,
    fetchall: bool = False,
    commit: bool = False,
) -> Any:
    params = params or ()
    with db_cursor(commit=commit) as cursor:
        cursor.execute(query, params)
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        return cursor.lastrowid


def executescript(script: str) -> None:
    with db_cursor(commit=True) as cursor:
        cursor.executescript(script)


def initialize_database() -> None:
    logger.info("Inicializando banco de dados...")
    from . import migrations  # import local para evitar ciclos

    conn = get_connection()
    migrations.create_tables(conn)
    migrations.seed_initial_data(conn)
    logger.info("Banco de dados pronto.")


def close_connection() -> None:
    conn: Optional[sqlite3.Connection] = getattr(_thread_local, "connection", None)
    if conn is not None:
        conn.close()
        _thread_local.connection = None


__all__ = [
    "get_connection",
    "db_cursor",
    "execute",
    "executescript",
    "initialize_database",
    "close_connection",
]
