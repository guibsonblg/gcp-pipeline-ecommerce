# Scripts Utilitários

Esta pasta contém scripts utilitários para a pipeline.

## generate_mock_data.py

Script para gerar dados mockados de e-commerce usando a biblioteca Faker.

### Dependências

```bash
pip install -r requirements.txt
```

### Uso

```bash
python generate_mock_data.py
```

### O que é gerado

O script cria um arquivo JSON com três entidades principais:

- **clientes**: Dados de clientes (100 registros por padrão)
  - Informações pessoais, endereço, segmento de cliente
  - Datas de registro variadas nos últimos 2 anos

- **produtos**: Catálogo de produtos (50 registros por padrão)
  - Produtos de diferentes categorias (Eletrônicos, Roupas, etc.)
  - Preços, custos, estoques e fornecedores variados

- **transacoes**: Transações de vendas (500 registros por padrão)
  - Vendas entre clientes e produtos
  - Quantidades, preços, datas e status variados
  - Métodos de pagamento diversos

### Formato do Arquivo de Saída

```
ecommerce-data-YYYYMMDD-HHMMSS.json
```

### Personalização

Para alterar a quantidade de dados gerados, edite as chamadas das funções no final do script:

```python
customers = generate_customers(100)    # Número de clientes
products = generate_products(50)       # Número de produtos
transactions = generate_transactions(customers, products, 500)  # Número de transações
```

### Exemplo de Uso na Pipeline

1. Gere os dados: `python generate_mock_data.py`
2. Faça upload do arquivo JSON gerado no bucket GCS
3. A pipeline será acionada automaticamente