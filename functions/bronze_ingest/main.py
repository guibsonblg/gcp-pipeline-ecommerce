import base64
import json
import os
from datetime import datetime

from google.cloud import bigquery, pubsub_v1, storage

project_id = os.environ.get("GCP_PROJECT_ID")
bronze_dataset = os.environ.get("BRONZE_DATASET", "bronze")
pubsub_topic = os.environ.get("PUBSUB_TOPIC")

storage_client = storage.Client()
bq_client = bigquery.Client()
publisher = pubsub_v1.PublisherClient()


def ingest_to_bronze(event, context):
    """Processa arquivo JSON e insere dados na camada Bronze."""
    bucket_name = event.get("bucket")
    object_name = event.get("name")

    if not bucket_name or not object_name:
        raise ValueError("Evento GCS não contém nome do bucket ou objeto")

    # Verificar se é um arquivo JSON de dados
    if not object_name.endswith('.json'):
        return {
            "status": "ignorado",
            "message": f"Arquivo {object_name} não é JSON, ignorando ingestão",
        }

    blob = storage_client.bucket(bucket_name).blob(object_name)
    content = blob.download_as_text(encoding="utf-8")
    data = json.loads(content)

    if not isinstance(data, dict) or 'clientes' not in data or 'produtos' not in data or 'transacoes' not in data:
        raise ValueError("Formato de dados inválido. Esperado JSON com clientes, produtos e transacoes")

    loaded_at = datetime.utcnow().isoformat("T") + "Z"
    total_rows = 0

    # Processar clientes
    customers_rows = []
    for customer in data['clientes']:
        customers_rows.append({
            "id_cliente": customer["id_cliente"],
            "nome": customer["nome"],
            "email": customer["email"],
            "telefone": customer.get("telefone"),
            "endereco": customer.get("endereco"),
            "cidade": customer.get("cidade"),
            "estado": customer.get("estado"),
            "pais": customer.get("pais"),
            "data_cadastro": customer["data_cadastro"],
            "carregado_em": loaded_at,
        })

    if customers_rows:
        customers_table_id = f"{project_id}.{bronze_dataset}.clientes"
        customers_errors = bq_client.insert_rows_json(customers_table_id, customers_rows)
        if customers_errors:
            raise RuntimeError(f"Falha ao inserir clientes na tabela Bronze: {customers_errors}")
        total_rows += len(customers_rows)

    # Processar produtos
    products_rows = []
    for product in data['produtos']:
        products_rows.append({
            "id_produto": product["id_produto"],
            "nome": product["nome"],
            "categoria": product["categoria"],
            "subcategoria": product.get("subcategoria"),
            "preco": product["preco"],
            "custo": product.get("custo"),
            "quantidade_estoque": product["quantidade_estoque"],
            "fornecedor": product.get("fornecedor"),
            "criado_em": product["criado_em"],
            "carregado_em": loaded_at,
        })

    if products_rows:
        products_table_id = f"{project_id}.{bronze_dataset}.produtos"
        products_errors = bq_client.insert_rows_json(products_table_id, products_rows)
        if products_errors:
            raise RuntimeError(f"Falha ao inserir produtos na tabela Bronze: {products_errors}")
        total_rows += len(products_rows)

    # Processar transações
    transactions_rows = []
    for transaction in data['transacoes']:
        transactions_rows.append({
            "id_transacao": transaction["id_transacao"],
            "id_cliente": transaction["id_cliente"],
            "id_produto": transaction["id_produto"],
            "quantidade": transaction["quantidade"],
            "preco_unitario": transaction["preco_unitario"],
            "valor_total": transaction["valor_total"],
            "data_transacao": transaction["data_transacao"],
            "status": transaction["status"],
            "metodo_pagamento": transaction.get("metodo_pagamento"),
            "carregado_em": loaded_at,
        })

    if transactions_rows:
        transactions_table_id = f"{project_id}.{bronze_dataset}.transacoes"
        transactions_errors = bq_client.insert_rows_json(transactions_table_id, transactions_rows)
        if transactions_errors:
            raise RuntimeError(f"Falha ao inserir transações na tabela Bronze: {transactions_errors}")
        total_rows += len(transactions_rows)

    if total_rows == 0:
        return {
            "status": "vazio",
            "message": f"Nenhuma linha encontrada em {object_name}",
        }

    message = json.dumps({
        "arquivo_origem": object_name,
        "linhas_carregadas": total_rows,
        "quantidade_clientes": len(customers_rows),
        "quantidade_produtos": len(products_rows),
        "quantidade_transacoes": len(transactions_rows)
    })
    topic_path = publisher.topic_path(project_id, pubsub_topic)
    publisher.publish(topic_path, message.encode("utf-8"))

    return {
        "status": "sucesso",
        "linhas_carregadas": total_rows,
        "quantidade_clientes": len(customers_rows),
        "quantidade_produtos": len(products_rows),
        "quantidade_transacoes": len(transactions_rows),
        "topico_publicado": pubsub_topic,
    }
