# Arquitetura Técnica — Scale-to-Insight

## 1. Visão Geral

A arquitetura "Scale-to-Insight" migra um monólito e-commerce para um ecossistema de dados integrado com duas responsabilidades principais:

1. **Operacional**: Servir APIs de vendas e análise financeira
2. **Analítico**: Pipeline de dados para inteligência de negócio

## 2. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────┐
│                  CAMADA DE SERVIÇOS                 │
│                                                     │
│  ┌─────────┐    ┌────────────┐  ┌───────────────┐  │
│  │ Cliente │───>│   Nginx    │─>│ API Vendas    │  │
│  │ HTTP    │    │  (Proxy)   │  │ (FastAPI:8000)│  │
│  └─────────┘    │            │  └───────┬───────┘  │
│                 │            │          │           │
│                 │            │  ┌───────▼───────┐  │
│                 └────────────┘  │ API Financeiro│  │
│                                 │ (FastAPI:8001)│  │
│                                 └───────┬───────┘  │
└─────────────────────────────────────────┼───────────┘
                                          │
┌─────────────────────────────────────────▼───────────┐
│                  CAMADA DE DADOS                    │
│                                                     │
│  ┌───────────────┐    ┌──────────────────────────┐ │
│  │  LocalStack   │    │    Data Lake (Raw)        │ │
│  │  S3: s3://    │    │    data/raw/              │ │
│  │  SQS: queues  │    │    ├── sales/             │ │
│  └───────────────┘    │    ├── financial/         │ │
│                        │    └── logs/              │ │
│                        └──────────────────────────┘ │
│                                     │               │
│                        ┌────────────▼─────────────┐ │
│                        │    ETL Pipeline          │ │
│                        │    pipelines/etl/        │ │
│                        │    ├── extract.py        │ │
│                        │    ├── transform.py      │ │
│                        │    └── load.py           │ │
│                        └────────────┬─────────────┘ │
│                                     │               │
│                        ┌────────────▼─────────────┐ │
│                        │  Data Warehouse           │ │
│                        │  PostgreSQL:5432          │ │
│                        │  ├── dim_produto          │ │
│                        │  ├── dim_cliente          │ │
│                        │  ├── dim_data             │ │
│                        │  ├── fato_vendas          │ │
│                        │  └── fato_financeiro      │ │
│                        └────────────┬─────────────┘ │
│                                     │               │
│                        ┌────────────▼─────────────┐ │
│                        │    Data Marts BI          │ │
│                        │  ├── mart_performance_    │ │
│                        │  │     vendas (View)      │ │
│                        │  └── mart_saude_          │ │
│                        │        financeira (View)  │ │
│                        └──────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## 3. Fluxo de Dados

```
[API Vendas] ──┐
               ├──> [LocalStack S3] ──> [Data Lake Raw]
[API Financeiro]─┘        │
       │                   └──> [SQS Events]
       │                              │
       └──────────────────────────────┤
                                      ▼
                              [ETL Pipeline]
                             Extract → Transform → Load
                                      │
                                      ▼
                            [PostgreSQL Warehouse]
                            dim_* + fato_* tables
                                      │
                                      ▼
                              [Data Mart Views]
                            Performance + Saúde
```

## 4. Decisões Técnicas

### 4.1 FastAPI vs Flask
- **Escolha**: FastAPI
- **Motivo**: Melhor performance, validação automática com Pydantic, documentação OpenAPI integrada, suporte async nativo

### 4.2 PostgreSQL para Data Warehouse
- **Escolha**: PostgreSQL 15
- **Motivo**: ACID compliant, suporte a Views para Data Marts, excelente suporte a Star Schema, open-source

### 4.3 LocalStack vs Cloud Real
- **Escolha**: LocalStack
- **Motivo**: Desenvolvimento local sem custos, simulação fiel de S3 e SQS, portabilidade

### 4.4 ETL com Python Scripts vs Airflow
- **Escolha**: Python scripts + DAG Airflow
- **Motivo**: Scripts simples para execução manual, DAG para orquestração em produção

### 4.5 Star Schema
- Otimizado para queries analíticas de BI
- Simplicidade de joins (menos tabelas)
- Compatível com ferramentas de BI padrão

## 5. Segurança

- Variáveis de ambiente para credenciais (não hardcoded)
- Validação de input com Pydantic models
- Health checks nos serviços
- Redes Docker isoladas (ada-network)

## 6. Escalabilidade

- Nginx preparado para load balancing entre múltiplas instâncias
- Serviços stateless (prontos para horizontal scaling)
- Data Lake para armazenamento histórico ilimitado
- Views materializáveis para Data Marts de alta performance
