# Pipeline Medallion GCP

Pipeline de dados orientada a eventos no Google Cloud Platform com arquitetura **Medallion (Bronze → Silver → Analytics)** para dados de e-commerce. Infraestrutura provisionada via Terraform e deploy automatizado via GitHub Actions.

## Arquitetura

```
                    ┌─────────────────────────────────────────────────────┐
                    │               Google Cloud Platform                 │
                    │                                                     │
  Upload JSON  ───► │  GCS Bucket (raw)                                   │
                    │       │                                             │
                    │       │ trigger (object.finalize)                   │
                    │       ▼                                             │
                    │  Cloud Function: bronze_ingest                      │
                    │       │  · valida estrutura do JSON                 │
                    │       │  · insere no BigQuery Bronze                │
                    │       │  · publica no Pub/Sub                       │
                    │       ▼                                             │
                    │  Pub/Sub: bronze-to-silver                          │
                    │       │                                             │
                    │       │ trigger (message)                           │
                    │       ▼                                             │
                    │  Cloud Function: silver_transform                   │
                    │       │  · deduplica (QUALIFY ROW_NUMBER)           │
                    │       │  · normaliza strings (TRIM/UPPER/LOWER)     │
                    │       │  · calcula margem_lucro                     │
                    │       │  · valida status e consistência financeira  │
                    │       │  · insere no BigQuery Silver                │
                    │       │  · publica no Pub/Sub                       │
                    │       ▼                                             │
                    │  Pub/Sub: silver-to-analytics                       │
                    │       │                                             │
                    │       │ trigger (message)                           │
                    │       ▼                                             │
                    │  Cloud Function: analytics_views                    │
                    │       │  · cria/atualiza 6 views analíticas         │
                    │       ▼                                             │
                    │  BigQuery Analytics (views)                         │
                    └─────────────────────────────────────────────────────┘
```

### Camadas de dados

| Camada | Dataset BQ | Descrição |
|---|---|---|
| Bronze | `bronze` | Ingestão bruta append-only, timestamp de carga |
| Silver | `silver` | Dados limpos, deduplicados, enriquecidos (`margem_lucro`) |
| Analytics | `analytics` | Views agregadas para consumo analítico |

## Stack

- **Infraestrutura**: Terraform 1.6+, GCS backend para estado remoto
- **Processamento**: Python 3.11, Cloud Functions Gen 1
- **Armazenamento**: Google Cloud Storage, BigQuery
- **Orquestração**: Pub/Sub (event-driven, sem orquestrador centralizado)
- **CI/CD**: GitHub Actions (fmt → validate → apply → deploy)
- **Segurança**: Service Accounts com least-privilege, Workload Identity-ready

## Regras de data quality (Silver)

- **Deduplicação**: `QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY carregado_em DESC) = 1`
- **Normalização**: `TRIM()` em strings, `UPPER()` em `estado`, `LOWER()` em `email`
- **Filtros de integridade**: registros nulos em campos obrigatórios são descartados
- **Validação de status**: apenas `completed`, `pending` e `cancelled` são aceitos
- **Consistência financeira**: `|quantidade × preco_unitario - valor_total| ≤ 0.01`
- **Enriquecimento**: `margem_lucro = (preco - custo) / preco`

## Views analíticas

| View | Descrição |
|---|---|
| `resumo_clientes` | Métricas por cliente: total gasto, número de pedidos, datas |
| `performance_produtos` | Receita, quantidade vendida e preço médio por produto |
| `vendas_por_categoria` | Receita e volume agregados por categoria/subcategoria |
| `vendas_diarias` | Série temporal de vendas com clientes únicos por dia |
| `valor_vida_cliente` | CLV com segmentação (Alto / Médio / Baixo Valor) |
| `status_inventario` | Estoque atual com alertas (Esgotado / Estoque Baixo) |

## Estrutura do Repositório

```
gcp-pipeline/
├── .github/
│   └── workflows/
│       └── pipeline.yml         # CI/CD: Terraform + deploy
├── functions/
│   ├── bronze_ingest/
│   │   ├── main.py              # GCS trigger → BigQuery Bronze
│   │   └── requirements.txt
│   ├── silver_transform/
│   │   ├── main.py              # Pub/Sub trigger → transformações Silver
│   │   └── requirements.txt
│   └── analytics_views/
│       ├── main.py              # Pub/Sub trigger → views Analytics
│       └── requirements.txt
├── terraform/
│   ├── main.tf                  # Todos os recursos GCP
│   ├── variables.tf
│   ├── versions.tf              # Backend GCS + versões dos providers
│   └── schemas/                 # Schemas JSON das tabelas BigQuery
│       ├── bronze_clientes.json
│       ├── bronze_produtos.json
│       ├── bronze_transacoes.json
│       ├── silver_clientes.json
│       ├── silver_produtos.json
│       └── silver_transacoes.json
├── scripts/
│   ├── generate_mock_data.py    # Gerador de dados mockados com Faker
│   └── requirements.txt
└── sample_data/
    └── ecommerce-sample.json    # Dados de exemplo para testes rápidos
```

## Observações

- Projetado para utilizar apenas serviços dentro da camada gratuita do GCP.
- Cloud Functions Gen 1 (flag `--no-gen2`) para compatibilidade com o SDK atual.
- O estado do Terraform é armazenado no mesmo bucket GCS usado para ingestão de dados.
