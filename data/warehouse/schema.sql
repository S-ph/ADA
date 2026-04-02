-- Dimensões
CREATE TABLE IF NOT EXISTS dim_produto (
    produto_id VARCHAR(50) PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    categoria VARCHAR(100),
    preco DECIMAL(10,2),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_cliente (
    cliente_id VARCHAR(50) PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    cidade VARCHAR(100),
    segmento VARCHAR(50),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_data (
    data_id SERIAL PRIMARY KEY,
    data DATE NOT NULL,
    dia INT,
    mes INT,
    trimestre INT,
    ano INT,
    dia_semana VARCHAR(20),
    UNIQUE(data)
);

CREATE TABLE IF NOT EXISTS dim_financeiro (
    transacao_id VARCHAR(50) PRIMARY KEY,
    tipo VARCHAR(50),
    status VARCHAR(50),
    moeda VARCHAR(10) DEFAULT 'BRL',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fatos
CREATE TABLE IF NOT EXISTS fato_vendas (
    venda_id VARCHAR(50) PRIMARY KEY,
    produto_id VARCHAR(50) REFERENCES dim_produto(produto_id),
    cliente_id VARCHAR(50) REFERENCES dim_cliente(cliente_id),
    data_id INT REFERENCES dim_data(data_id),
    quantidade INT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fato_financeiro (
    id SERIAL PRIMARY KEY,
    transacao_id VARCHAR(50) REFERENCES dim_financeiro(transacao_id),
    venda_id VARCHAR(50) REFERENCES fato_vendas(venda_id),
    valor_custo DECIMAL(10,2),
    margem DECIMAL(10,2),
    status_pagamento VARCHAR(50),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data Mart: Performance de Vendas
CREATE OR REPLACE VIEW mart_performance_vendas AS
SELECT
    dp.nome AS produto,
    dp.categoria,
    dc.cidade,
    dd.mes,
    dd.ano,
    SUM(fv.quantidade) AS total_quantidade,
    SUM(fv.valor) AS receita_total,
    COUNT(fv.venda_id) AS total_vendas
FROM fato_vendas fv
JOIN dim_produto dp ON fv.produto_id = dp.produto_id
JOIN dim_cliente dc ON fv.cliente_id = dc.cliente_id
JOIN dim_data dd ON fv.data_id = dd.data_id
GROUP BY dp.nome, dp.categoria, dc.cidade, dd.mes, dd.ano;

-- Data Mart: Saúde Financeira
CREATE OR REPLACE VIEW mart_saude_financeira AS
SELECT
    dd.mes,
    dd.ano,
    SUM(fv.valor) AS receita_bruta,
    SUM(ff.valor_custo) AS custo_total,
    SUM(fv.valor - ff.valor_custo) AS margem_bruta,
    CASE WHEN SUM(fv.valor) > 0
        THEN (SUM(fv.valor - ff.valor_custo) / SUM(fv.valor)) * 100
        ELSE 0
    END AS percentual_margem,
    COUNT(DISTINCT fv.venda_id) AS total_vendas
FROM fato_vendas fv
JOIN fato_financeiro ff ON fv.venda_id = ff.venda_id
JOIN dim_data dd ON fv.data_id = dd.data_id
GROUP BY dd.mes, dd.ano;
