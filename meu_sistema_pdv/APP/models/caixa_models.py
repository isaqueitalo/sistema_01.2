from __future__ import annotations

from typing import List, Optional

from APP.core.database import execute, get_connection
from APP.core.logger import get_logger
from APP.core.utils import gerar_chave_unica

logger = get_logger()


def caixa_aberto(usuario_id: Optional[int] = None):
    if usuario_id:
        return execute(
            "SELECT * FROM caixas WHERE status = 'aberto' AND usuario_id = ? ORDER BY aberto_em DESC LIMIT 1",
            (usuario_id,),
            fetchone=True,
        )
    return execute(
        "SELECT * FROM caixas WHERE status = 'aberto' ORDER BY aberto_em DESC LIMIT 1",
        fetchone=True,
    )


def abrir_caixa(usuario_id: int, valor_abertura: float):
    conn = get_connection()
    with conn:
        cursor = conn.cursor()
        codigo = gerar_chave_unica("CX")
        cursor.execute(
            """
            INSERT INTO caixas (codigo, usuario_id, aberto_em, valor_abertura, status)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, 'aberto')
            """,
            (codigo, usuario_id, valor_abertura),
        )
        caixa_id = cursor.lastrowid
    logger.info("Caixa %s aberto por usuário %s", codigo, usuario_id)
    return caixa_id


def registrar_movimento(
    caixa_id: int,
    *,
    tipo: str,
    valor: float,
    forma_pagamento: str,
    venda_id: Optional[int] = None,
    descricao: str | None = None,
) -> None:
    execute(
        """
        INSERT INTO caixa_movimentos (
            caixa_id,
            tipo,
            valor,
            forma_pagamento,
            referencia_venda_id,
            descricao
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (caixa_id, tipo, valor, forma_pagamento, venda_id, descricao),
        commit=True,
    )


def total_por_forma(caixa_id: int) -> List:
    return execute(
        """
        SELECT forma_pagamento, SUM(valor) AS total
        FROM caixa_movimentos
        WHERE caixa_id = ?
        GROUP BY forma_pagamento
        """,
        (caixa_id,),
        fetchall=True,
    )


def fechar_caixa(caixa_id: int, valor_fechamento: float) -> None:
    execute(
        """
        UPDATE caixas
        SET status = 'fechado',
            fechado_em = CURRENT_TIMESTAMP,
            valor_fechamento = ?
        WHERE id = ?
        """,
        (valor_fechamento, caixa_id),
        commit=True,
    )
    logger.info("Caixa %s fechado.", caixa_id)


def relatorio_caixas(inicio: str, fim: str) -> List:
    return execute(
        """
        SELECT
            c.*,
            u.nome AS operador,
            COALESCE(SUM(m.valor), 0) AS total_movimentado,
            COALESCE(SUM(CASE WHEN m.tipo = 'venda' THEN m.valor ELSE 0 END), 0) AS total_vendas
        FROM caixas c
        JOIN usuarios u ON u.id = c.usuario_id
        LEFT JOIN caixa_movimentos m ON m.caixa_id = c.id
        WHERE c.aberto_em BETWEEN ? AND ?
        GROUP BY c.id
        ORDER BY c.aberto_em DESC
        """,
        (inicio, fim),
        fetchall=True,
    )


def total_saidas_periodo(inicio: str, fim: str) -> float:
    row = execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM caixa_movimentos
        WHERE tipo = 'saida_caixa' AND criado_em BETWEEN ? AND ?
        """,
        (inicio, fim),
        fetchone=True,
    )
    return abs(float(row["total"] if row else 0))


def saidas_por_periodo(inicio: str, fim: str) -> List:
    return execute(
        """
        SELECT descricao, valor, criado_em
        FROM caixa_movimentos
        WHERE tipo = 'saida_caixa' AND criado_em BETWEEN ? AND ?
        ORDER BY criado_em DESC
        """,
        (inicio, fim),
        fetchall=True,
    )


def total_perdas_periodo(inicio: str, fim: str) -> float:
    row = execute(
        """
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM caixa_movimentos
        WHERE tipo = 'perda' AND criado_em BETWEEN ? AND ?
        """,
        (inicio, fim),
        fetchone=True,
    )
    return abs(float(row["total"] if row else 0))


def perdas_por_periodo(inicio: str, fim: str) -> List:
    return execute(
        """
        SELECT descricao, valor, criado_em
        FROM caixa_movimentos
        WHERE tipo = 'perda' AND criado_em BETWEEN ? AND ?
        ORDER BY criado_em DESC
        """,
        (inicio, fim),
        fetchall=True,
    )


__all__ = [
    "caixa_aberto",
    "abrir_caixa",
    "registrar_movimento",
    "total_por_forma",
    "fechar_caixa",
    "relatorio_caixas",
    "total_saidas_periodo",
    "saidas_por_periodo",
    "total_perdas_periodo",
    "perdas_por_periodo",
]
