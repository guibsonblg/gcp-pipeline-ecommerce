#!/usr/bin/env python3
"""
Script para gerar dados mockados de e-commerce para a pipeline Medallion.

Gera dados para três entidades:
- customers: dados dos clientes
- products: catálogo de produtos
- transactions: transações de vendas

Salva tudo em um único arquivo JSON para ingestão na pipeline.
"""

import json
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('pt_BR')  # Usar dados brasileiros para localização

def generate_customers(num_customers=100):
    """Gera dados de clientes."""
    customers = []
    segments = ['Bronze', 'Prata', 'Ouro', 'Platinum']

    for i in range(num_customers):
        customer_id = f"CUST-{i+1:04d}"
        registration_date = fake.date_between(start_date='-2y', end_date='today')

        customer = {
            'id_cliente': customer_id,
            'nome': fake.name(),
            'email': fake.email(),
            'telefone': fake.phone_number(),
            'endereco': fake.street_address(),
            'cidade': fake.city(),
            'estado': fake.state_abbr(),
            'pais': 'Brasil',
            'data_cadastro': registration_date.isoformat(),
            'segmento_cliente': random.choice(segments)
        }
        customers.append(customer)

    return customers

def generate_products(num_products=50):
    """Gera catálogo de produtos."""
    products = []
    categories = {
        'Eletrônicos': ['Smartphones', 'Notebooks', 'Tablets', 'Fones de Ouvido', 'Smartwatches'],
        'Roupas': ['Camisetas', 'Calças', 'Vestidos', 'Jaquetas', 'Tênis'],
        'Casa': ['Móveis', 'Decoração', 'Eletrodomésticos', 'Utensílios', 'Cama e Mesa'],
        'Livros': ['Ficção', 'Não Ficção', 'Técnicos', 'Infantis', 'Didáticos'],
        'Esportes': ['Bicicletas', 'Equipamentos', 'Roupas Esportivas', 'Suplementos']
    }

    suppliers = ['Amazon', 'Magazine Luiza', 'Americanas', 'Mercado Livre', 'Shopee', 'AliExpress']

    for i in range(num_products):
        product_id = f"PROD-{i+1:04d}"
        category = random.choice(list(categories.keys()))
        subcategory = random.choice(categories[category])

        base_price = random.uniform(10, 2000)
        cost = base_price * random.uniform(0.3, 0.7)  # Custo entre 30-70% do preço

        product = {
            'id_produto': product_id,
            'nome': fake.sentence(nb_words=3)[:-1],  # Remove o ponto final
            'categoria': category,
            'subcategoria': subcategory,
            'preco': round(base_price, 2),
            'custo': round(cost, 2),
            'quantidade_estoque': random.randint(0, 500),
            'fornecedor': random.choice(suppliers),
            'criado_em': fake.date_time_between(start_date='-1y', end_date='today').isoformat()
        }
        products.append(product)

    return products

def generate_transactions(customers, products, num_transactions=500):
    """Gera transações de vendas."""
    transactions = []
    statuses = ['completed', 'pending', 'cancelled', 'refunded']
    payment_methods = ['credit_card', 'debit_card', 'pix', 'boleto', 'paypal']

    for i in range(num_transactions):
        transaction_id = f"TXN-{i+1:06d}"
        customer = random.choice(customers)
        product = random.choice(products)

        quantity = random.randint(1, 5)
        unit_price = product['preco'] * random.uniform(0.8, 1.2)  # Variação de preço
        total_amount = round(unit_price * quantity, 2)

        # Transações mais recentes têm maior probabilidade
        days_back = random.choices(
            [7, 30, 90, 365],
            weights=[0.4, 0.3, 0.2, 0.1]
        )[0]
        transaction_date = datetime.now() - timedelta(days=random.randint(0, days_back))

        transaction = {
            'id_transacao': transaction_id,
            'id_cliente': customer['id_cliente'],
            'id_produto': product['id_produto'],
            'quantidade': quantity,
            'preco_unitario': round(unit_price, 2),
            'valor_total': total_amount,
            'data_transacao': transaction_date.isoformat(),
            'status': random.choices(statuses, weights=[0.7, 0.15, 0.1, 0.05])[0],
            'metodo_pagamento': random.choice(payment_methods)
        }
        transactions.append(transaction)

    return transactions

def main():
    """Gera dados mockados e salva em arquivo JSON."""
    print("Gerando dados mockados de e-commerce...")

    # Gerar dados
    customers = generate_customers(100)
    products = generate_products(50)
    transactions = generate_transactions(customers, products, 500)

    # Estrutura final
    data = {
        'clientes': customers,
        'produtos': products,
        'transacoes': transactions,
        'generated_at': datetime.now().isoformat(),
        'version': '1.0'
    }

    # Salvar arquivo
    filename = f"ecommerce-data-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Arquivo gerado: {filename}")
    print(f"Clientes: {len(customers)}")
    print(f"Produtos: {len(products)}")
    print(f"Transações: {len(transactions)}")

if __name__ == '__main__':
    main()