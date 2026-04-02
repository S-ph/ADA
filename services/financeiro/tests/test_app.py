"""Tests for Financeiro API."""
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, transacoes_db

client = TestClient(app)

INITIAL_COUNT = 3  # seeded mock data


@pytest.fixture(autouse=True)
def reset_db():
    original = transacoes_db.copy()
    yield
    transacoes_db.clear()
    transacoes_db.extend(original)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "financeiro"}


def test_list_transacoes():
    response = client.get("/transacoes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == INITIAL_COUNT


def test_create_transacao_valid():
    payload = {
        "venda_id": "V999",
        "valor_custo": 50.0,
        "moeda": "BRL",
        "tipo": "pagamento",
        "status": "aprovado",
    }
    response = client.post("/transacoes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["venda_id"] == "V999"
    assert data["valor_custo"] == 50.0
    assert "transacao_id" in data


def test_create_transacao_missing_fields():
    payload = {"venda_id": "V999"}
    response = client.post("/transacoes", json=payload)
    assert response.status_code == 422


def test_get_transacao_by_id():
    response = client.get("/transacoes/T001")
    assert response.status_code == 200
    assert response.json()["transacao_id"] == "T001"


def test_get_transacao_not_found():
    response = client.get("/transacoes/NONEXISTENT")
    assert response.status_code == 404


def test_relatorio_saude_financeira():
    response = client.get("/relatorios/saude-financeira")
    assert response.status_code == 200
    data = response.json()
    assert "receita_total" in data
    assert "custo_total" in data
    assert "margem_lucro" in data
    assert "total_transacoes" in data
    assert data["total_transacoes"] == INITIAL_COUNT


def test_relatorio_performance_vendas():
    response = client.get("/relatorios/performance-vendas")
    assert response.status_code == 200
    data = response.json()
    assert "total_transacoes" in data
    assert "ticket_medio" in data
    assert "por_status" in data
    assert "por_tipo" in data
