"""Sales API - FastAPI application."""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Vendas API", version="1.0.0")

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
S3_BUCKET = os.getenv("S3_BUCKET", "ada-data-lake")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "http://localhost:4566/000000000000/vendas-events")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# In-memory storage
vendas_db: list = []

PRODUTOS_MOCK = [
    {"produto_id": "P001", "nome": "Notebook Pro", "categoria": "Eletrônicos", "preco": 4999.99},
    {"produto_id": "P002", "nome": "Mouse Wireless", "categoria": "Periféricos", "preco": 149.99},
    {"produto_id": "P003", "nome": "Teclado Mecânico", "categoria": "Periféricos", "preco": 299.99},
    {"produto_id": "P004", "nome": "Monitor 4K", "categoria": "Eletrônicos", "preco": 2499.99},
    {"produto_id": "P005", "nome": "Headset Gamer", "categoria": "Acessórios", "preco": 399.99},
]


class VendaCreate(BaseModel):
    produto_id: str
    cliente_id: str
    quantidade: int
    valor: float

    @field_validator("quantidade")
    @classmethod
    def quantidade_positiva(cls, v):
        if v <= 0:
            raise ValueError("quantidade must be positive")
        return v

    @field_validator("valor")
    @classmethod
    def valor_positivo(cls, v):
        if v <= 0:
            raise ValueError("valor must be positive")
        return v


class Venda(BaseModel):
    venda_id: str
    produto_id: str
    cliente_id: str
    quantidade: int
    valor: float
    data: str
    status: str = "pendente"


def get_boto3_client(service: str):
    return boto3.client(
        service,
        endpoint_url=AWS_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_DEFAULT_REGION,
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "vendas"}


@app.get("/produtos", response_model=List[dict])
def list_produtos():
    logger.info("Listing products")
    return PRODUTOS_MOCK


@app.post("/vendas", response_model=Venda, status_code=201)
def create_venda(venda: VendaCreate):
    nova_venda = Venda(
        venda_id=f"V{uuid.uuid4().hex[:8].upper()}",
        produto_id=venda.produto_id,
        cliente_id=venda.cliente_id,
        quantidade=venda.quantidade,
        valor=venda.valor,
        data=datetime.now().strftime("%Y-%m-%d"),
        status="pendente",
    )
    vendas_db.append(nova_venda.model_dump())
    logger.info(f"Created sale {nova_venda.venda_id}")
    return nova_venda


@app.get("/vendas", response_model=List[Venda])
def list_vendas():
    logger.info(f"Listing {len(vendas_db)} sales")
    return vendas_db


@app.get("/vendas/{venda_id}", response_model=Venda)
def get_venda(venda_id: str):
    for venda in vendas_db:
        if venda["venda_id"] == venda_id:
            return venda
    raise HTTPException(status_code=404, detail=f"Venda {venda_id} not found")


@app.post("/vendas/{venda_id}/exportar")
def exportar_venda(venda_id: str):
    venda = None
    for v in vendas_db:
        if v["venda_id"] == venda_id:
            venda = v
            break

    if venda is None:
        raise HTTPException(status_code=404, detail=f"Venda {venda_id} not found")

    results = {"venda_id": venda_id, "s3": None, "sqs": None, "errors": []}

    # Upload to S3
    try:
        s3 = get_boto3_client("s3")
        key = f"sales/{venda['data']}/{venda_id}.json"
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(venda, default=str),
            ContentType="application/json",
        )
        results["s3"] = f"s3://{S3_BUCKET}/{key}"
        logger.info(f"Exported sale {venda_id} to S3: {key}")
    except ClientError as e:
        error_msg = f"S3 error: {e}"
        results["errors"].append(error_msg)
        logger.warning(error_msg)

    # Send SQS message
    try:
        sqs = get_boto3_client("sqs")
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps({"event": "venda_exportada", "venda_id": venda_id, "data": venda}),
        )
        results["sqs"] = "message sent"
        logger.info(f"SQS message sent for sale {venda_id}")
    except ClientError as e:
        error_msg = f"SQS error: {e}"
        results["errors"].append(error_msg)
        logger.warning(error_msg)

    return results
