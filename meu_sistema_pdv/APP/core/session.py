from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class UserSession:
    id: int
    username: str
    nome: str
    role: str


class SessionManager:
    def __init__(self) -> None:
        self._user: Optional[UserSession] = None

    def login(self, user_row) -> UserSession:
        self._user = UserSession(
            id=user_row["id"],
            username=user_row["username"],
            nome=user_row["nome"],
            role=user_row["role"],
        )
        return self._user

    def logout(self) -> None:
        self._user = None

    @property
    def user(self) -> Optional[UserSession]:
        return self._user

    def is_authenticated(self) -> bool:
        return self._user is not None

    def has_role(self, *roles: str) -> bool:
        if not self._user:
            return False
        return self._user.role in roles


session = SessionManager()

__all__ = ["SessionManager", "session", "UserSession"]
