# Decisões Técnicas

## Stack Escolhido

| Componente | Tecnologia | Justificativa |
|------------|------------|---------------|
| APIs | Python + FastAPI | Performance, validação, docs automáticas |
| Proxy | Nginx | Estável, performático, configurável |
| Banco de Dados | PostgreSQL 15 | ACID, open-source, BI-friendly |
| Cloud Emulado | LocalStack | Gratuito, offline, portável |
| ETL | Python Scripts | Simplicidade, flexibilidade |
| Orquestração | Apache Airflow | Padrão de mercado, DAGs |
| CI/CD | GitHub Actions | Integrado ao repositório |

## Padrões Adotados

- **REST API**: Interface padrão e bem conhecida
- **Star Schema**: Modelo dimensional para Data Warehouse
- **12-Factor App**: Configuração por variáveis de ambiente
- **Health Checks**: Todos os serviços expõem /health
