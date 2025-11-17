from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import date, datetime
from typing import Tuple


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}:{hashed.hex()}"


def check_password(password: str, hashed: str) -> bool:
    try:
        salt_hex, hashed_hex = hashed.split(":")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    stored = bytes.fromhex(hashed_hex)
    new_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(new_hash, stored)


def gerar_chave_unica(prefixo: str = "COD") -> str:
    token = secrets.token_hex(4).upper()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{prefixo}-{timestamp}-{token}"


def format_currency(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def hoje_intervalo() -> Tuple[str, str]:
    hoje = date.today()
    inicio = datetime.combine(hoje, datetime.min.time())
    fim = datetime.combine(hoje, datetime.max.time())
    return inicio.isoformat(), fim.isoformat()


def mes_atual_intervalo() -> Tuple[str, str]:
    hoje = date.today()
    inicio = datetime(hoje.year, hoje.month, 1)
    if hoje.month == 12:
        fim = datetime(hoje.year + 1, 1, 1)
    else:
        fim = datetime(hoje.year, hoje.month + 1, 1)
    return inicio.isoformat(), fim.isoformat()


__all__ = [
    "hash_password",
    "check_password",
    "gerar_chave_unica",
    "format_currency",
    "hoje_intervalo",
    "mes_atual_intervalo",
]
