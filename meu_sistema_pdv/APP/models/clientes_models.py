from __future__ import annotations

from typing import List, Optional

from APP.core.database import execute


def listar_clientes(busca: Optional[str] = None) -> List:
    if busca:
        like = f"%{busca.upper()}%"
        return execute(
            """
            SELECT * FROM clientes
            WHERE UPPER(nome) LIKE ? OR UPPER(documento) LIKE ?
            ORDER BY nome
            """,
            (like, like),
            fetchall=True,
        )
    return execute("SELECT * FROM clientes ORDER BY nome", fetchall=True)


def obter_cliente(cliente_id: int):
    return execute(
        "SELECT * FROM clientes WHERE id = ?",
        (cliente_id,),
        fetchone=True,
    )


def criar_cliente(
    nome: str,
    documento: Optional[str],
    telefone: Optional[str],
    email: Optional[str],
    observacoes: Optional[str],
) -> int:
    return execute(
        """
        INSERT INTO clientes (nome, documento, telefone, email, observacoes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nome, documento, telefone, email, observacoes),
        commit=True,
    )


def atualizar_cliente(
    cliente_id: int,
    nome: str,
    documento: Optional[str],
    telefone: Optional[str],
    email: Optional[str],
    observacoes: Optional[str],
) -> None:
    execute(
        """
        UPDATE clientes
        SET nome = ?, documento = ?, telefone = ?, email = ?, observacoes = ?
        WHERE id = ?
        """,
        (nome, documento, telefone, email, observacoes, cliente_id),
        commit=True,
    )


def excluir_cliente(cliente_id: int) -> None:
    execute("DELETE FROM clientes WHERE id = ?", (cliente_id,), commit=True)


__all__ = [
    "listar_clientes",
    "obter_cliente",
    "criar_cliente",
    "atualizar_cliente",
    "excluir_cliente",
]
