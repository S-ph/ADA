# Relatório Técnico — Scale-to-Insight

## 1. EXECUTIVO (Resumo)

O projeto **Scale-to-Insight** propõe a migração de um monólito de e-commerce para um **ecossistema de dados moderno**, integrando uma camada operacional (APIs de vendas e finanças) com uma camada analítica (data lake + data warehouse + data marts). O objetivo central é **suportar picos de tráfego** e **gerar inteligência de negócio em tempo real** para o setor financeiro.

**Objetivos técnicos alcançados:**
- Substituição do monólito por **dois serviços independentes** (Vendas e Financeiro).
- Uso de **proxy reverso (Nginx)** como ponto de entrada.
- Simulação de cloud com **LocalStack (S3 + SQS)**.
- Implementação de **pipeline ETL** em Python.
- Modelagem de **Data Warehouse** com **Star Schema** e **Data Marts**.

**Escopo de entrega:**
- Infraestrutura completa com Docker/Docker Compose.
- Arquitetura documentada no README e ARQUITETURA.md.
- Relatório técnico com decisões arquiteturais + diagramas.

## 2. ARQUITETURA GERAL

### Diagrama de Atores e Componentes (ASCII)

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
│                        │  ├── mart_performance_    │
│                        │  │     vendas (View)      │
│                        │  └── mart_saude_          │
│                        │        financeira (View)  │
│                        └──────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Fluxo de Dados Completo

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

## 3. DECISÕES ARQUITETURAIS DETALHADAS

### 3.1 FastAPI vs Flask
- **Problema identificado:** necessidade de APIs rápidas, tipadas e com documentação automática.
- **Opções consideradas:** Flask ou FastAPI.
- **Solução adotada:** FastAPI.
- **Justificativa:** performance superior, suporte async, validação Pydantic e OpenAPI.
- **Trade-offs:** curva de aprendizado ligeiramente maior.
- **Impacto na arquitetura:** APIs modernas, padronizadas e escaláveis.

### 3.2 PostgreSQL como Data Warehouse
- **Problema identificado:** necessidade de analytics com integridade transacional.
- **Opções consideradas:** PostgreSQL, MySQL, soluções cloud.
- **Solução adotada:** PostgreSQL 15.
- **Justificativa:** ACID, suporte a Views e Star Schema, open-source.
- **Trade-offs:** menor elasticidade comparado a soluções cloud.
- **Impacto na arquitetura:** data marts consistentes e consultas analíticas confiáveis.

### 3.3 LocalStack vs Cloud Real (AWS)
- **Problema identificado:** simulação de serviços cloud com custo zero.
- **Opções consideradas:** AWS Free Tier ou LocalStack.
- **Solução adotada:** LocalStack.
- **Justificativa:** desenvolvimento local, sem custos, portável.
- **Trade-offs:** limitações frente à AWS real.
- **Impacto na arquitetura:** ambiente totalmente reproduzível em Docker.

### 3.4 Python Scripts + Airflow DAGs
- **Problema identificado:** ETL precisa ser simples localmente e escalável em produção.
- **Opções consideradas:** apenas scripts ou somente Airflow.
- **Solução adotada:** Python scripts + DAG Airflow.
- **Justificativa:** execução manual rápida + orquestração futura.
- **Trade-offs:** manutenção dupla (scripts + DAGs).
- **Impacto na arquitetura:** flexibilidade no desenvolvimento e produção.

### 3.5 Star Schema vs Dimensional Modeling
- **Problema identificado:** modelo de dados analítico eficiente.
- **Opções consideradas:** snowflake, 3NF ou star schema.
- **Solução adotada:** Star Schema.
- **Justificativa:** simplicidade e desempenho analítico.
- **Trade-offs:** redundância de dados.
- **Impacto na arquitetura:** otimização para BI.

### 3.6 Nginx como Proxy Reverso
- **Problema identificado:** unificar entrada e gerenciar tráfego.
- **Opções consideradas:** API Gateway dedicado ou Nginx.
- **Solução adotada:** Nginx.
- **Justificativa:** simples, leve, suporte a load balancing.
- **Trade-offs:** menos recursos avançados comparado a gateways cloud.
- **Impacto na arquitetura:** escalabilidade horizontal pronta.

### 3.7 Docker Compose para Orquestração Local
- **Problema identificado:** necessidade de ambiente reproduzível local.
- **Opções consideradas:** Kubernetes ou Compose.
- **Solução adotada:** Docker Compose.
- **Justificativa:** simplicidade, setup rápido, ideal para projeto acadêmico.
- **Trade-offs:** não adequado para produção complexa.
- **Impacto na arquitetura:** onboarding rápido e padronizado.

## 4. COMPONENTES E RESPONSABILIDADES

| Componente | Tecnologia | Porta | Função |
|---|---|---|---|
| Proxy Reverso | Nginx | 80 | Entry point, load balancing |
| API Vendas | FastAPI | 8000 | CRUD vendas, eventos |
| API Financeiro | FastAPI | 8001 | Análise financeira, relatórios |
| Cloud Simulation | LocalStack | 4566 | S3 + SQS simulados |
| ETL | Python | N/A | Extract, Transform, Load |
| Data Warehouse | PostgreSQL | 5432 | Star Schema, dimensões e fatos |
| Data Marts | SQL Views | N/A | Performance Vendas, Saúde Financeira |

## 5. DIAGRAMA TÉCNICO DETALHADO

### 5.1 Diagrama de Sequência (Venda → Data Mart)

```
Cliente → API Vendas → LocalStack(S3) → Data Lake Raw
                                  → SQS → ETL Pipeline
ETL → PostgreSQL (fato_vendas + dimensões) → Views BI
```

### 5.2 Diagrama de Deployment (Docker)

```
[Docker Network: ada-network]
  ├── nginx (80)
  ├── vendas-api (8000)
  ├── financeiro-api (8001)
  ├── localstack (4566)
  ├── postgres (5432)
  └── etl (execução manual)
```

### 5.3 Diagrama de Dados (Star Schema)

```
dim_produto
 dim_cliente
 dim_data
 dim_financeiro
      |
      |---- fato_vendas
      |---- fato_financeiro
```

## 6. PADRÕES E PRINCÍPIOS APLICADOS

- **Microserviços:** separação Vendas ↔ Financeiro
- **API-First:** interfaces RESTful padronizadas
- **Stateless:** serviços prontos para scaling horizontal
- **ACID:** garantias transacionais no warehouse
- **ELT Pattern:** dados brutos preservados, transformação posterior
- **Isolamento de Rede:** Docker networks isoladas

## 7. ESCALABILIDADE

- **Nginx** permite múltiplas instâncias de serviço.
- **Data Lake** suporta crescimento histórico ilimitado.
- **Views** podem ser materializadas para BI.
- **Particionamento** possível em tabelas de fatos.

## 8. SEGURANÇA E BOAS PRÁTICAS

- Variáveis de ambiente para credenciais.
- Validação de input (Pydantic).
- Health checks nos serviços.
- Sem secrets hardcoded.
- Redes Docker isoladas.

## 9. CI/CD E AUTOMAÇÃO

Workflows descritos no README:
- **build.yml** — build imagens Docker
- **test.yml** — testes unitários e schemas
- **deploy.yml** — deploy local com Compose

## 10. CONCLUSÕES

A solução **atende integralmente o enunciado do Projeto Final**, incluindo:
- Duas APIs de microserviço
- Proxy reverso
- Simulação de cloud com LocalStack
- Pipeline ETL completo
- Data Lake + Warehouse + Data Mart
- Automação CI/CD

**Pontos fortes:**
- Arquitetura clara e escalável
- Integração total entre operação e analytics
- Documentação rica

**Possíveis melhorias futuras:**
- Migrar LocalStack → AWS real
- Orquestrar ETL com Airflow completo
- Adicionar observabilidade (logs/metrics/traces)