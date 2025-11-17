from __future__ import annotations

from typing import Iterable

from .session import session

SECTION_ROLES = {
    "usuarios": {"admin"},
    "logs": {"admin"},
    "config": {"admin"},
    "relatorios": {"gerente", "admin"},
    "caixa": {"gerente", "admin"},
    "pdv": {"vendedor", "gerente", "admin"},
    "produtos": {"vendedor", "gerente", "admin"},
}


def require_role(*roles: str) -> bool:
    """Return True if the current user has at least one of the desired roles."""
    return session.has_role(*roles)


def can_access(section: str) -> bool:
    roles = SECTION_ROLES.get(section)
    if roles is None:
        return session.is_authenticated()
    return require_role(*roles)


def ensure_permission(section: str) -> None:
    if not can_access(section):
        raise PermissionError(
            f"Usuário sem permissão para acessar o módulo '{section}'."
        )


def has_any_role(roles: Iterable[str]) -> bool:
    return require_role(*roles)


__all__ = [
    "require_role",
    "can_access",
    "ensure_permission",
    "has_any_role",
    "SECTION_ROLES",
]
