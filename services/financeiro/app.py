"""Financial API - FastAPI application."""
import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Financeiro API", version="1.0.0")

# In-memory storage
transacoes_db: list = [
    {
        "transacao_id": "T001",
        "venda_id": "V001",
        "valor": 199.98,
        "valor_custo": 120.00,
        "moeda": "BRL",
        "tipo": "pagamento",
        "status": "aprovado",
        "data": "2026-01-15",
    },
    {
        "transacao_id": "T002",
        "venda_id": "V002",
        "valor": 299.99,
        "valor_custo": 180.00,
        "moeda": "BRL",
        "tipo": "pagamento",
        "status": "aprovado",
        "data": "2026-01-16",
    },
    {
        "transacao_id": "T003",
        "venda_id": "V003",
        "valor": 449.97,
        "valor_custo": 270.00,
        "moeda": "BRL",
        "tipo": "pagamento",
        "status": "pendente",
        "data": "2026-01-17",
    },
]


class TransacaoCreate(BaseModel):
    venda_id: str
    valor_custo: float
    moeda: str = "BRL"
    tipo: str
    status: str

    @field_validator("valor_custo")
    @classmethod
    def custo_nao_negativo(cls, v):
        if v < 0:
            raise ValueError("valor_custo must be non-negative")
        return v


class Transacao(BaseModel):
    transacao_id: str
    venda_id: str
    valor: float = 0.0
    valor_custo: float
    moeda: str = "BRL"
    tipo: str
    status: str
    data: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "financeiro"}


@app.get("/transacoes", response_model=List[dict])
def list_transacoes():
    logger.info(f"Listing {len(transacoes_db)} transactions")
    return transacoes_db


@app.post("/transacoes", response_model=dict, status_code=201)
def create_transacao(transacao: TransacaoCreate):
    nova = {
        "transacao_id": f"T{uuid.uuid4().hex[:8].upper()}",
        "venda_id": transacao.venda_id,
        "valor": 0.0,
        "valor_custo": transacao.valor_custo,
        "moeda": transacao.moeda,
        "tipo": transacao.tipo,
        "status": transacao.status,
        "data": datetime.now().strftime("%Y-%m-%d"),
    }
    transacoes_db.append(nova)
    logger.info(f"Created transaction {nova['transacao_id']}")
    return nova


@app.get("/transacoes/{transacao_id}", response_model=dict)
def get_transacao(transacao_id: str):
    for t in transacoes_db:
        if t["transacao_id"] == transacao_id:
            return t
    raise HTTPException(status_code=404, detail=f"Transacao {transacao_id} not found")


@app.get("/relatorios/saude-financeira")
def saude_financeira():
    receita_total = sum(t.get("valor", 0) for t in transacoes_db)
    custo_total = sum(t.get("valor_custo", 0) for t in transacoes_db)
    margem_bruta = receita_total - custo_total
    margem_lucro = (margem_bruta / receita_total * 100) if receita_total > 0 else 0.0
    total_transacoes = len(transacoes_db)
    aprovadas = sum(1 for t in transacoes_db if t.get("status") == "aprovado")
    logger.info("Generated financial health report")
    return {
        "receita_total": round(receita_total, 2),
        "custo_total": round(custo_total, 2),
        "margem_bruta": round(margem_bruta, 2),
        "margem_lucro": round(margem_lucro, 2),
        "total_transacoes": total_transacoes,
        "transacoes_aprovadas": aprovadas,
        "taxa_aprovacao": round((aprovadas / total_transacoes * 100) if total_transacoes > 0 else 0, 2),
        "gerado_em": datetime.now().isoformat(),
    }


@app.get("/relatorios/performance-vendas")
def performance_vendas():
    por_status: dict = {}
    por_tipo: dict = {}
    for t in transacoes_db:
        status = t.get("status", "desconhecido")
        tipo = t.get("tipo", "desconhecido")
        por_status[status] = por_status.get(status, 0) + 1
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    ticket_medio = (
        sum(t.get("valor", 0) for t in transacoes_db) / len(transacoes_db)
        if transacoes_db else 0
    )
    logger.info("Generated sales performance report")
    return {
        "total_transacoes": len(transacoes_db),
        "ticket_medio": round(ticket_medio, 2),
        "por_status": por_status,
        "por_tipo": por_tipo,
        "gerado_em": datetime.now().isoformat(),
    }
