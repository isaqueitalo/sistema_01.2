from __future__ import annotations

import sqlite3
from datetime import datetime

from .config import get_config
from .logger import get_logger
from .utils import hash_password

logger = get_logger()


CREATE_SCRIPT = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    senha_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','gerente','vendedor')),
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco_venda REAL NOT NULL DEFAULT 0,
    estoque REAL NOT NULL DEFAULT 0,
    estoque_minimo REAL NOT NULL DEFAULT 0,
    codigo_barras TEXT,
    categoria TEXT,
    data_validade TEXT,
    lote TEXT,
    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    documento TEXT,
    telefone TEXT,
    email TEXT,
    observacoes TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    usuario_id INTEGER NOT NULL,
    cliente_id INTEGER,
    total_bruto REAL NOT NULL DEFAULT 0,
    desconto_percentual REAL NOT NULL DEFAULT 0,
    total_liquido REAL NOT NULL DEFAULT 0,
    forma_pagamento TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE IF NOT EXISTS venda_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade REAL NOT NULL DEFAULT 1,
    preco_unitario REAL NOT NULL DEFAULT 0,
    total_item REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id INTEGER NOT NULL,
    forma_pagamento TEXT NOT NULL,
    valor REAL NOT NULL,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS caixas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    usuario_id INTEGER NOT NULL,
    aberto_em TEXT NOT NULL,
    fechado_em TEXT,
    valor_abertura REAL NOT NULL DEFAULT 0,
    valor_fechamento REAL,
    status TEXT NOT NULL DEFAULT 'aberto',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS caixa_movimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caixa_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    forma_pagamento TEXT,
    valor REAL NOT NULL,
    referencia_venda_id INTEGER,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (caixa_id) REFERENCES caixas(id),
    FOREIGN KEY (referencia_venda_id) REFERENCES vendas(id)
);

CREATE TABLE IF NOT EXISTS configuracoes_loja (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    nome TEXT,
    cnpj TEXT,
    endereco TEXT,
    telefone TEXT,
    logo TEXT
);

CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome);
CREATE INDEX IF NOT EXISTS idx_vendas_data ON vendas(criado_em);
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);
"""


def create_tables(conn: sqlite3.Connection) -> None:
    logger.debug("Aplicando script de criação de tabelas.")
    conn.executescript(CREATE_SCRIPT)
    conn.commit()


def seed_initial_data(conn: sqlite3.Connection) -> None:
    cfg = get_config()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM usuarios WHERE username = ?", (cfg.default_admin["username"],)
    )
    if cursor.fetchone() is None:
        logger.info("Criando usuário padrão: %s", cfg.default_admin["username"])
        cursor.execute(
            """
            INSERT INTO usuarios (username, nome, senha_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                cfg.default_admin["username"],
                "Administrador",
                hash_password(cfg.default_admin["password"]),
                cfg.default_admin.get("role", "admin"),
            ),
        )

    cursor.execute("SELECT 1 FROM clientes WHERE nome = ?", ("Consumidor Final",))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO clientes (nome, documento) VALUES (?, ?)",
            ("Consumidor Final", "000.000.000-00"),
        )

    cursor.execute("SELECT 1 FROM configuracoes_loja WHERE id = 1")
    if cursor.fetchone() is None:
        company = cfg.company
        cursor.execute(
            """
            INSERT INTO configuracoes_loja (id, nome, cnpj, endereco, telefone, logo)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (
                company.get("name", cfg.app_name),
                company.get("cnpj", ""),
                company.get("address", ""),
                company.get("phone", ""),
                company.get("logo", ""),
            ),
        )

    conn.commit()
    logger.debug("Dados iniciais aplicados em %s", datetime.utcnow().isoformat())


__all__ = ["create_tables", "seed_initial_data"]
