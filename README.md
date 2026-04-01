# Scale-to-Insight — Ecossistema de Dados

> Projeto Final — Caixaverso Módulo 2  
> Arquitetura moderna e escalável para migração de e-commerce monolítico para ecossistema de dados integrado

## 🏗️ Arquitetura

```
Internet → Nginx (Proxy) → [ Serviço Vendas | Serviço Financeiro ]
                                    ↓
                           LocalStack (S3 + SQS)
                                    ↓
                            ETL Pipeline (Python)
                                    ↓
                      Data Lake (Raw) → Data Warehouse (PostgreSQL)
                                    ↓
                              Data Mart BI
```

## 📦 Serviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Nginx | 80 | Proxy reverso e load balancer |
| Vendas API | 8000 | API de e-commerce e vendas |
| Financeiro API | 8001 | API financeira e analytics |
| PostgreSQL | 5432 | Data Warehouse |
| LocalStack | 4566 | Simulação AWS (S3 + SQS) |

## 🚀 Quick Start

### Pré-requisitos
- Docker 24+
- Docker Compose 2.20+

### Subir o ambiente completo

```bash
# Clone o repositório
git clone https://github.com/S-ph/ADA.git
cd ADA

# Subir todos os serviços
docker compose up -d

# Verificar status
docker compose ps
```

### Endpoints disponíveis

```bash
# Via Nginx (porta 80)
curl http://localhost/health
curl http://localhost/vendas/health
curl http://localhost/vendas/produtos
curl http://localhost/financeiro/health
curl http://localhost/financeiro/relatorios/saude-financeira

# Direto nos serviços
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Criar uma venda

```bash
curl -X POST http://localhost:8000/vendas \
  -H "Content-Type: application/json" \
  -d '{
    "produto_id": "P001",
    "cliente_id": "C001",
    "quantidade": 2,
    "valor": 199.98
  }'
```

## 🧪 Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio httpx

# Testar serviço de vendas
cd services/vendas
pytest tests/ -v

# Testar serviço financeiro
cd services/financeiro
pytest tests/ -v
```

## 🔄 ETL Pipeline

```bash
# Executar pipeline ETL manualmente
cd pipelines/etl
pip install -r requirements.txt
python main.py
```

## 📊 Estrutura de Dados

### Data Lake (Raw)
```
data/
├── raw/
│   ├── sales/YYYY-MM-DD/sales.json
│   ├── financial/YYYY-MM-DD/transactions.json
│   └── logs/YYYY-MM-DD/
└── processed/
```

### Data Warehouse (Star Schema)
- **Dimensões**: dim_produto, dim_cliente, dim_data, dim_financeiro
- **Fatos**: fato_vendas, fato_financeiro
- **Data Marts**: mart_performance_vendas, mart_saude_financeira

## 🤖 CI/CD

GitHub Actions workflows:
- **build.yml** — Build das imagens Docker
- **test.yml** — Testes unitários e validação de schemas
- **deploy.yml** — Deploy local com Docker Compose

## 📁 Estrutura do Repositório

```
ADA/
├── README.md
├── ARQUITETURA.md
├── docker-compose.yml
├── services/
│   ├── vendas/         # API de Vendas (FastAPI)
│   ├── financeiro/     # API Financeira (FastAPI)
│   └── nginx/          # Proxy Reverso
├── data/
│   ├── raw/            # Data Lake
│   ├── processed/
│   └── warehouse/      # Schema SQL
├── pipelines/
│   ├── etl/            # Scripts ETL
│   └── dags/           # Airflow DAGs
├── infra/
│   └── localstack/     # Simulação AWS
└── .github/workflows/  # CI/CD
```
