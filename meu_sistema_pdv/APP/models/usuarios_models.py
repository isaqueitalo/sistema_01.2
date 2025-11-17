from __future__ import annotations

from typing import Iterable, List, Optional

from APP.core.database import execute
from APP.core.logger import get_logger
from APP.core.utils import check_password, hash_password

logger = get_logger()


def listar_usuarios() -> List:
    return execute(
        "SELECT id, username, nome, role, ativo, criado_em FROM usuarios ORDER BY nome",
        fetchall=True,
    )


def obter_usuario(usuario_id: int):
    return execute(
        "SELECT * FROM usuarios WHERE id = ?",
        (usuario_id,),
        fetchone=True,
    )


def buscar_por_username(username: str):
    return execute(
        "SELECT * FROM usuarios WHERE username = ?",
        (username,),
        fetchone=True,
    )


def criar_usuario(nome: str, username: str, senha: str, role: str) -> int:
    senha_hash = hash_password(senha)
    logger.info("Criando usuário %s (%s)", username, role)
    return execute(
        """
        INSERT INTO usuarios (nome, username, senha_hash, role)
        VALUES (?, ?, ?, ?)
        """,
        (nome, username, senha_hash, role),
        commit=True,
    )


def atualizar_usuario(
    usuario_id: int,
    *,
    nome: str,
    role: str,
    senha: Optional[str] = None,
) -> None:
    if senha:
        execute(
            """
            UPDATE usuarios
            SET nome = ?, role = ?, senha_hash = ?
            WHERE id = ?
            """,
            (nome, role, hash_password(senha), usuario_id),
            commit=True,
        )
    else:
        execute(
            "UPDATE usuarios SET nome = ?, role = ? WHERE id = ?",
            (nome, role, usuario_id),
            commit=True,
        )


def alterar_status(usuario_id: int, ativo: bool) -> None:
    execute(
        "UPDATE usuarios SET ativo = ? WHERE id = ?",
        (1 if ativo else 0, usuario_id),
        commit=True,
    )


def excluir_usuario(usuario_id: int) -> None:
    execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,), commit=True)


def autenticar(username: str, senha: str):
    usuario = buscar_por_username(username)
    if usuario and usuario["ativo"] and check_password(senha, usuario["senha_hash"]):
        logger.info("Usuário %s autenticado", username)
        return usuario
    logger.warning("Falha de login para %s", username)
    return None


def atualizar_senha(usuario_id: int, nova_senha: str) -> None:
    execute(
        "UPDATE usuarios SET senha_hash = ? WHERE id = ?",
        (hash_password(nova_senha), usuario_id),
        commit=True,
    )


def usuarios_por_role(roles: Iterable[str]) -> List:
    marcadores = ",".join("?" * len(tuple(roles)))
    return execute(
        f"SELECT * FROM usuarios WHERE role IN ({marcadores})",
        tuple(roles),
        fetchall=True,
    )


__all__ = [
    "listar_usuarios",
    "obter_usuario",
    "buscar_por_username",
    "criar_usuario",
    "atualizar_usuario",
    "alterar_status",
    "excluir_usuario",
    "autenticar",
    "atualizar_senha",
    "usuarios_por_role",
]
