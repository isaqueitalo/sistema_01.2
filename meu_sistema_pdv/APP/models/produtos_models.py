from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from APP.core.database import execute
from APP.core.logger import get_logger

logger = get_logger()


def listar_produtos(busca: Optional[str] = None) -> List:
    if busca:
        like = f"%{busca.upper()}%"
        return execute(
            """
            SELECT * FROM produtos
            WHERE UPPER(nome) LIKE ?
               OR UPPER(codigo_barras) LIKE ?
            ORDER BY nome
            """,
            (like, like),
            fetchall=True,
        )
    return execute("SELECT * FROM produtos ORDER BY nome", fetchall=True)


def obter_produto(produto_id: int):
    return execute(
        "SELECT * FROM produtos WHERE id = ?",
        (produto_id,),
        fetchone=True,
    )


def buscar_por_codigo(codigo: str):
    return execute(
        "SELECT * FROM produtos WHERE codigo_barras = ?",
        (codigo,),
        fetchone=True,
    )


def buscar_por_nome(fragmento: str):
    frase = f"%{fragmento.upper()}%"
    return execute(
        "SELECT * FROM produtos WHERE UPPER(nome) LIKE ? ORDER BY nome LIMIT 1",
        (frase,),
        fetchone=True,
    )


def buscar_sugestoes(termo: str, limite: int = 5) -> List:
    like = f"%{termo.upper()}%"
    return execute(
        """
        SELECT * FROM produtos
        WHERE UPPER(nome) LIKE ?
           OR UPPER(codigo_barras) LIKE ?
        ORDER BY nome
        LIMIT ?
        """,
        (like, like, limite),
        fetchall=True,
    )


def criar_produto(
    nome: str,
    preco_venda: float,
    estoque: float,
    estoque_minimo: float,
    *,
    codigo_barras: Optional[str] = None,
    categoria: Optional[str] = None,
    data_validade: Optional[str] = None,
    lote: Optional[str] = None,
) -> int:
    logger.info("Cadastrando produto %s", nome)
    return execute(
        """
        INSERT INTO produtos
        (nome, preco_venda, estoque, estoque_minimo, codigo_barras, categoria, data_validade, lote)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            preco_venda,
            estoque,
            estoque_minimo,
            codigo_barras,
            categoria,
            data_validade,
            lote,
        ),
        commit=True,
    )


def atualizar_produto(
    produto_id: int,
    *,
    nome: str,
    preco_venda: float,
    estoque: float,
    estoque_minimo: float,
    codigo_barras: Optional[str],
    categoria: Optional[str],
    data_validade: Optional[str],
    lote: Optional[str],
) -> None:
    execute(
        """
        UPDATE produtos
        SET nome = ?, preco_venda = ?, estoque = ?, estoque_minimo = ?,
            codigo_barras = ?, categoria = ?, data_validade = ?, lote = ?,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            nome,
            preco_venda,
            estoque,
            estoque_minimo,
            codigo_barras,
            categoria,
            data_validade,
            lote,
            produto_id,
        ),
        commit=True,
    )


def excluir_produto(produto_id: int) -> None:
    execute("DELETE FROM produtos WHERE id = ?", (produto_id,), commit=True)


def atualizar_estoque(produto_id: int, delta: float) -> None:
    execute(
        "UPDATE produtos SET estoque = estoque + ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
        (delta, produto_id),
        commit=True,
    )


def produtos_estoque_baixo() -> List:
    return execute(
        "SELECT * FROM produtos WHERE estoque < estoque_minimo ORDER BY nome",
        fetchall=True,
    )


def produtos_proximos_validade(dias: int = 15) -> List:
    limite = (datetime.now() + timedelta(days=dias)).date().isoformat()
    return execute(
        """
        SELECT * FROM produtos
        WHERE data_validade IS NOT NULL
          AND data_validade <= ?
        ORDER BY data_validade
        """,
        (limite,),
        fetchall=True,
    )


__all__ = [
    "listar_produtos",
    "obter_produto",
    "buscar_por_codigo",
    "buscar_por_nome",
    "buscar_sugestoes",
    "criar_produto",
    "atualizar_produto",
    "excluir_produto",
    "atualizar_estoque",
    "produtos_estoque_baixo",
    "produtos_proximos_validade",
]
