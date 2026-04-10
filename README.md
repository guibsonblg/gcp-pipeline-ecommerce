# Pipeline GCP

Uma pipeline simples em GCP com arquitetura Medallion (Bronze, Silver, Gold/Analytics) para dados de e-commerce:

- Ingestão manual via upload de arquivo JSON no bucket GCS
- Cloud Functions para processar o arquivo e avançar o pipeline
- BigQuery para Bronze e Silver
- Views no dataset Analytics (Gold)
- Terraform para provisionar infraestrutura
- GitHub Actions para executar Terraform e deploy das funções

## Arquitetura

- `raw` bucket: ingestão manual de arquivos JSON com dados de e-commerce
- Bronze: dataset BigQuery com tabelas de ingestão (clientes, produtos, transacoes)
- Silver: dataset BigQuery com tabelas transformadas e limpas
- Analytics: dataset BigQuery com views analíticas derivadas
- Cloud Functions:
  - `bronze_ingest`: processa o arquivo JSON e separa dados para Bronze
  - `silver_transform`: transforma Bronze em Silver (limpeza e enriquecimento)
  - `analytics_views`: cria/atualiza views analíticas em Analytics

## Estrutura de Dados

### Clientes (clientes)
- id_cliente, nome, email, telefone, endereco, cidade, estado, pais
- data_cadastro, segmento_cliente

### Produtos (produtos)
- id_produto, nome, categoria, subcategoria, preco, custo
- quantidade_estoque, fornecedor, criado_em, margem_lucro

### Transações (transacoes)
- id_transacao, id_cliente, id_produto, quantidade, preco_unitario, valor_total
- data_transacao, status, metodo_pagamento

## Deploy

1. Criar secrets no GitHub:
   - `GCP_PROJECT_ID`
   - `GCP_REGION`
   - `GCP_LOCATION` (por exemplo `US`)
   - `GCP_SA_KEY` (JSON da service account base64 ou diretamente como JSON)

2. Executar o workflow GitHub Actions:
   - `pipeline.yml` para aplicar infra e deploy das funções

## Geração de Dados de Teste

Para gerar dados mockados para teste:

```bash
cd scripts
pip install -r requirements.txt
python generate_mock_data.py
```

Isso criará um arquivo `ecommerce-data-YYYYMMDD-HHMMSS.json` com:
- 100 clientes
- 50 produtos
- 500 transações

Ou use o arquivo de exemplo `sample_data/ecommerce-sample.json` para testes rápidos.

## Uso

1. Gere dados de teste ou crie seu próprio arquivo JSON seguindo o formato:
   ```json
   {
     "clientes": [...],
     "produtos": [...],
     "transacoes": [...],
     "generated_at": "...",
     "version": "1.0"
   }
   ```

2. Faça upload do arquivo JSON no bucket:
   - `gs://<project_id>-pipeline-raw`

3. A função `bronze_ingest` será acionada automaticamente.
4. O processo prossegue para Silver e Analytics via Pub/Sub.

## Views Analíticas Disponíveis

- `resumo_clientes`: Resumo por cliente com métricas de compra
- `performance_produtos`: Performance de produtos
- `vendas_por_categoria`: Vendas por categoria
- `vendas_diarias`: Vendas diárias
- `valor_vida_cliente`: Valor do tempo de vida do cliente
- `status_inventario`: Status do inventário

## Observação

Projetado para utilizar apenas serviços com camada gratuita do GCP: Cloud Storage, BigQuery, Pub/Sub e Cloud Functions.
