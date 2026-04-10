# Schemas BigQuery

Esta pasta contém os schemas das tabelas BigQuery organizados por camada e entidade.

## Estrutura

### Camada Bronze (Raw Data)
- `bronze_clientes.tf` - Schema da tabela de clientes brutos
- `bronze_produtos.tf` - Schema da tabela de produtos brutos
- `bronze_transacoes.tf` - Schema da tabela de transações brutas

### Camada Silver (Cleaned Data)
- `silver_clientes.tf` - Schema da tabela de clientes limpos
- `silver_produtos.tf` - Schema da tabela de produtos limpos
- `silver_transacoes.tf` - Schema da tabela de transações limpas

## Como usar

Os schemas são definidos como `locals` no Terraform e referenciados no `main.tf`:

```hcl
schema = jsonencode(local.bronze_clientes_schema)
```

## Convenções

- Nomes das colunas em português brasileiro
- Tipos de dados seguindo padrão BigQuery
- Campos obrigatórios marcados como `REQUIRED`
- Campos opcionais marcados como `NULLABLE`