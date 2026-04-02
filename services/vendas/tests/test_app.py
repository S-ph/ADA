"""Tests for Vendas API."""
import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, vendas_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    vendas_db.clear()
    yield
    vendas_db.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "vendas"}


def test_list_produtos():
    response = client.get("/produtos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "produto_id" in data[0]
    assert "nome" in data[0]


def test_create_venda_valid():
    payload = {
        "produto_id": "P001",
        "cliente_id": "C001",
        "quantidade": 2,
        "valor": 199.98,
    }
    response = client.post("/vendas", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["produto_id"] == "P001"
    assert data["cliente_id"] == "C001"
    assert data["quantidade"] == 2
    assert data["valor"] == 199.98
    assert "venda_id" in data
    assert "data" in data


def test_create_venda_missing_fields():
    payload = {"produto_id": "P001"}
    response = client.post("/vendas", json=payload)
    assert response.status_code == 422


def test_create_venda_invalid_quantidade():
    payload = {
        "produto_id": "P001",
        "cliente_id": "C001",
        "quantidade": 0,
        "valor": 100.0,
    }
    response = client.post("/vendas", json=payload)
    assert response.status_code == 422


def test_list_vendas_empty():
    response = client.get("/vendas")
    assert response.status_code == 200
    assert response.json() == []


def test_list_vendas():
    client.post("/vendas", json={"produto_id": "P001", "cliente_id": "C001", "quantidade": 1, "valor": 99.99})
    client.post("/vendas", json={"produto_id": "P002", "cliente_id": "C002", "quantidade": 3, "valor": 299.97})
    response = client.get("/vendas")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_venda_by_id():
    create_response = client.post(
        "/vendas",
        json={"produto_id": "P001", "cliente_id": "C001", "quantidade": 1, "valor": 99.99},
    )
    venda_id = create_response.json()["venda_id"]
    response = client.get(f"/vendas/{venda_id}")
    assert response.status_code == 200
    assert response.json()["venda_id"] == venda_id


def test_get_venda_not_found():
    response = client.get("/vendas/NONEXISTENT")
    assert response.status_code == 404
