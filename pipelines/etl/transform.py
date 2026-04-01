"""Transform raw data for the Data Warehouse."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def transform_products(raw_sales: list) -> list:
    """Extract unique products from sales data."""
    seen = set()
    products = []
    for sale in raw_sales:
        pid = sale.get("produto_id")
        if pid and pid not in seen:
            seen.add(pid)
            products.append({
                "produto_id": pid,
                "nome": sale.get("nome_produto", f"Produto {pid}"),
                "categoria": sale.get("categoria", "Geral"),
                "preco": float(sale.get("valor", 0)) / max(int(sale.get("quantidade", 1)), 1),
            })
    logger.info(f"Transformed {len(products)} products")
    return products


def transform_clients(raw_sales: list) -> list:
    """Extract unique clients from sales data."""
    seen = set()
    clients = []
    for sale in raw_sales:
        cid = sale.get("cliente_id")
        if cid and cid not in seen:
            seen.add(cid)
            clients.append({
                "cliente_id": cid,
                "nome": sale.get("nome_cliente", f"Cliente {cid}"),
                "cidade": sale.get("cidade", "São Paulo"),
                "segmento": sale.get("segmento", "B2C"),
            })
    logger.info(f"Transformed {len(clients)} clients")
    return clients


def transform_dates(raw_sales: list) -> list:
    """Extract unique dates from sales data."""
    seen = set()
    dates = []
    for sale in raw_sales:
        date_str = sale.get("data")
        if date_str and date_str not in seen:
            seen.add(date_str)
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append({
                    "data": date_str,
                    "dia": dt.day,
                    "mes": dt.month,
                    "trimestre": (dt.month - 1) // 3 + 1,
                    "ano": dt.year,
                    "dia_semana": dt.strftime("%A"),
                })
            except ValueError:
                pass
    logger.info(f"Transformed {len(dates)} dates")
    return dates


def transform_sales(raw_sales: list) -> list:
    """Transform raw sales to fact_vendas format."""
    sales = []
    for sale in raw_sales:
        sales.append({
            "venda_id": sale.get("venda_id"),
            "produto_id": sale.get("produto_id"),
            "cliente_id": sale.get("cliente_id"),
            "data": sale.get("data"),
            "quantidade": int(sale.get("quantidade", 0)),
            "valor": float(sale.get("valor", 0)),
        })
    logger.info(f"Transformed {len(sales)} sales")
    return sales


def transform_financial(raw_financial: list) -> list:
    """Transform raw financial data."""
    transactions = []
    for txn in raw_financial:
        valor = float(txn.get("valor", 0))
        custo = float(txn.get("valor_custo", valor * 0.6))
        transactions.append({
            "transacao_id": txn.get("transacao_id"),
            "venda_id": txn.get("venda_id"),
            "tipo": txn.get("tipo", "pagamento"),
            "status": txn.get("status", "aprovado"),
            "moeda": txn.get("moeda", "BRL"),
            "valor_custo": custo,
            "margem": valor - custo,
            "status_pagamento": txn.get("status", "aprovado"),
        })
    logger.info(f"Transformed {len(transactions)} financial transactions")
    return transactions
