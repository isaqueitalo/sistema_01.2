from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence

from APP.core.database import execute, get_connection
from APP.core.logger import get_logger
from APP.core.utils import gerar_chave_unica

logger = get_logger()

FORMAS_PAGAMENTO = [
    "Dinheiro",
    "Cheque",
    "Cartão Crédito",
    "Cartão Débito",
    "PIX",
    "Vale Alimentação",
    "Vale Presente",
    "Outros",
]


def registrar_venda(
    itens: Sequence[Dict],
    *,
    usuario_id: int,
    cliente_id: Optional[int],
    desconto_valor: float,
    pagamentos: Optional[Sequence[Dict[str, float]]] = None,
    forma_principal: Optional[str] = None,
) -> Dict:
    if not itens:
        raise ValueError("Carrinho vazio.")

    conn = get_connection()
    with conn:
        cursor = conn.cursor()
        total_bruto = sum(item["quantidade"] * item["preco_unitario"] for item in itens)
        desconto_valor = max(0, desconto_valor)
        desconto_valor = min(desconto_valor, total_bruto)
        total_liquido = total_bruto - desconto_valor
        codigo = gerar_chave_unica("VENDA")
        agora = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO vendas (codigo, usuario_id, cliente_id, total_bruto,
                desconto_percentual, total_liquido, forma_pagamento, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                codigo,
                usuario_id,
                cliente_id,
                total_bruto,
                desconto_valor,
                total_liquido,
                forma_principal or (pagamentos[0]["forma"] if pagamentos else "Dinheiro"),
                agora,
            ),
        )
        venda_id = cursor.lastrowid

        for item in itens:
            cursor.execute(
                """
                INSERT INTO venda_itens (venda_id, produto_id, quantidade, preco_unitario, total_item)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    venda_id,
                    item["produto_id"],
                    item["quantidade"],
                    item["preco_unitario"],
                    item["quantidade"] * item["preco_unitario"],
                ),
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )

        pagamentos = pagamentos or [
            {"forma": forma_principal or "Dinheiro", "valor": total_liquido}
        ]
        for pagamento in pagamentos:
            cursor.execute(
                """
                INSERT INTO pagamentos (venda_id, forma_pagamento, valor)
                VALUES (?, ?, ?)
                """,
                (venda_id, pagamento["forma"], pagamento["valor"]),
            )

    logger.info("Venda %s registrada com %d itens.", codigo, len(itens))
    return {
        "id": venda_id,
        "codigo": codigo,
        "total": total_liquido,
        "desconto_valor": desconto_valor,
        "criado_em": agora,
        "itens": itens,
        "pagamentos": pagamentos,
    }


def vendas_por_periodo(inicio: str, fim: str) -> List:
    return execute(
        """
        SELECT v.*, v.desconto_percentual AS desconto_valor, u.nome AS vendedor, c.nome AS cliente
        FROM vendas v
        LEFT JOIN usuarios u ON u.id = v.usuario_id
        LEFT JOIN clientes c ON c.id = v.cliente_id
        WHERE v.criado_em BETWEEN ? AND ?
        ORDER BY v.criado_em DESC
        """,
        (inicio, fim),
        fetchall=True,
    )


def total_vendas_periodo(inicio: str, fim: str) -> float:
    row = execute(
        "SELECT COALESCE(SUM(total_liquido), 0) AS total FROM vendas WHERE criado_em BETWEEN ? AND ?",
        (inicio, fim),
        fetchone=True,
    )
    return float(row["total"] if row else 0)


def quantidade_vendas_periodo(inicio: str, fim: str) -> int:
    row = execute(
        "SELECT COUNT(*) AS qtd FROM vendas WHERE criado_em BETWEEN ? AND ?",
        (inicio, fim),
        fetchone=True,
    )
    return int(row["qtd"] if row else 0)


def total_descontos_periodo(inicio: str, fim: str) -> float:
    row = execute(
        "SELECT COALESCE(SUM(desconto_percentual), 0) AS total FROM vendas WHERE criado_em BETWEEN ? AND ?",
        (inicio, fim),
        fetchone=True,
    )
    return float(row["total"] if row else 0)

def pagamentos_por_periodo(inicio: str, fim: str) -> List:
    return execute(
        """
        SELECT p.forma_pagamento, SUM(p.valor) AS total
        FROM pagamentos p
        INNER JOIN vendas v ON v.id = p.venda_id
        WHERE v.criado_em BETWEEN ? AND ?
        GROUP BY p.forma_pagamento
        ORDER BY total DESC
        """,
        (inicio, fim),
        fetchall=True,
    )


def produtos_mais_vendidos(inicio: str, fim: str, limite: int = 5) -> List:
    return execute(
        f"""
        SELECT pr.nome, SUM(vi.quantidade) AS quantidade
        FROM venda_itens vi
        JOIN vendas v ON v.id = vi.venda_id
        JOIN produtos pr ON pr.id = vi.produto_id
        WHERE v.criado_em BETWEEN ? AND ?
        GROUP BY pr.nome
        ORDER BY quantidade DESC
        LIMIT {limite}
        """,
        (inicio, fim),
        fetchall=True,
    )


def historico_por_cliente(cliente_id: int) -> List:
    return execute(
        """
        SELECT v.*, u.nome AS vendedor
        FROM vendas v
        JOIN usuarios u ON u.id = v.usuario_id
        WHERE v.cliente_id = ?
        ORDER BY v.criado_em DESC
        """,
        (cliente_id,),
        fetchall=True,
    )


def ultima_venda() -> Optional[Dict]:
    row = execute(
        "SELECT * FROM vendas ORDER BY id DESC LIMIT 1",
        fetchone=True,
    )
    if not row:
        return None
    itens = execute(
        "SELECT vi.*, p.nome FROM venda_itens vi JOIN produtos p ON p.id = vi.produto_id WHERE venda_id = ?",
        (row["id"],),
        fetchall=True,
    )
    pagamentos = execute(
        "SELECT * FROM pagamentos WHERE venda_id = ?",
        (row["id"],),
        fetchall=True,
    )
    return {"venda": row, "itens": itens, "pagamentos": pagamentos}


def itens_da_venda(venda_id: int):
    return execute(
        "SELECT vi.*, p.nome FROM venda_itens vi JOIN produtos p ON p.id = vi.produto_id WHERE venda_id = ?",
        (venda_id,),
        fetchall=True,
    )


__all__ = [
    "registrar_venda",
    "vendas_por_periodo",
    "total_vendas_periodo",
    "quantidade_vendas_periodo",
    "total_descontos_periodo",
    "pagamentos_por_periodo",
    "produtos_mais_vendidos",
    "historico_por_cliente",
    "ultima_venda",
    "itens_da_venda",
    "FORMAS_PAGAMENTO",
]
