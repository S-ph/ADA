"""Load transformed data into PostgreSQL Data Warehouse."""
import logging
import os

import psycopg2
from psycopg2.extras import execute_batch

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "warehouse"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def load_products(products: list, conn=None):
    """Load products into dim_produto."""
    if not products:
        return
    close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """INSERT INTO dim_produto (produto_id, nome, categoria, preco)
                   VALUES (%(produto_id)s, %(nome)s, %(categoria)s, %(preco)s)
                   ON CONFLICT (produto_id) DO UPDATE
                   SET nome=EXCLUDED.nome, categoria=EXCLUDED.categoria, preco=EXCLUDED.preco""",
                products,
            )
        conn.commit()
        logger.info(f"Loaded {len(products)} products")
    finally:
        if close:
            conn.close()


def load_clients(clients: list, conn=None):
    """Load clients into dim_cliente."""
    if not clients:
        return
    close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """INSERT INTO dim_cliente (cliente_id, nome, cidade, segmento)
                   VALUES (%(cliente_id)s, %(nome)s, %(cidade)s, %(segmento)s)
                   ON CONFLICT (cliente_id) DO UPDATE
                   SET nome=EXCLUDED.nome, cidade=EXCLUDED.cidade, segmento=EXCLUDED.segmento""",
                clients,
            )
        conn.commit()
        logger.info(f"Loaded {len(clients)} clients")
    finally:
        if close:
            conn.close()


def load_dates(dates: list, conn=None):
    """Load dates into dim_data."""
    if not dates:
        return
    close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_batch(
                cur,
                """INSERT INTO dim_data (data, dia, mes, trimestre, ano, dia_semana)
                   VALUES (%(data)s, %(dia)s, %(mes)s, %(trimestre)s, %(ano)s, %(dia_semana)s)
                   ON CONFLICT (data) DO NOTHING""",
                dates,
            )
        conn.commit()
        logger.info(f"Loaded {len(dates)} dates")
    finally:
        if close:
            conn.close()


def load_sales(sales: list, conn=None):
    """Load sales facts into fato_vendas."""
    if not sales:
        return
    close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            for sale in sales:
                cur.execute("SELECT data_id FROM dim_data WHERE data = %s", (sale["data"],))
                row = cur.fetchone()
                if row:
                    cur.execute(
                        """INSERT INTO fato_vendas (venda_id, produto_id, cliente_id, data_id, quantidade, valor)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           ON CONFLICT (venda_id) DO UPDATE
                           SET quantidade=EXCLUDED.quantidade, valor=EXCLUDED.valor""",
                        (sale["venda_id"], sale["produto_id"], sale["cliente_id"],
                         row[0], sale["quantidade"], sale["valor"]),
                    )
        conn.commit()
        logger.info(f"Loaded {len(sales)} sales facts")
    finally:
        if close:
            conn.close()


def load_financial(transactions: list, conn=None):
    """Load financial data."""
    if not transactions:
        return
    close = conn is None
    if conn is None:
        conn = get_connection()
    try:
        with conn.cursor() as cur:
            for txn in transactions:
                cur.execute(
                    """INSERT INTO dim_financeiro (transacao_id, tipo, status, moeda)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (transacao_id) DO NOTHING""",
                    (txn["transacao_id"], txn["tipo"], txn["status"], txn["moeda"]),
                )
                cur.execute(
                    """INSERT INTO fato_financeiro (transacao_id, venda_id, valor_custo, margem, status_pagamento)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (txn["transacao_id"], txn.get("venda_id"), txn["valor_custo"],
                     txn["margem"], txn["status_pagamento"]),
                )
        conn.commit()
        logger.info(f"Loaded {len(transactions)} financial transactions")
    finally:
        if close:
            conn.close()
