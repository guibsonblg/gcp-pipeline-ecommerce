import base64
import json
import os

from google.cloud import bigquery, pubsub_v1

project_id = os.environ.get("GCP_PROJECT_ID")
bronze_dataset = os.environ.get("BRONZE_DATASET", "bronze")
silver_dataset = os.environ.get("SILVER_DATASET", "silver")
pubsub_topic = os.environ.get("PUBSUB_TOPIC")

bq_client = bigquery.Client()
publisher = pubsub_v1.PublisherClient()


def transform_to_silver(event, context):
    """Transforma dados da camada Bronze para Silver."""
    payload = {}
    if event.get("data"):
        payload = json.loads(base64.b64decode(event["data"]).decode("utf-8"))

    # Transformar clientes
    transform_customers()

    # Transformar produtos
    transform_products()

    # Transformar transações
    transform_transactions()

    message = json.dumps({
        "payload": payload,
        "silver_dataset": silver_dataset,
        "tabelas_transformadas": ["clientes", "produtos", "transacoes"],
    })
    topic_path = publisher.topic_path(project_id, pubsub_topic)
    publisher.publish(topic_path, message.encode("utf-8"))

    return {
        "status": "sucesso",
        "payload": payload,
        "silver_dataset": silver_dataset,
        "tabelas_transformadas": ["clientes", "produtos", "transacoes"],
    }


def transform_customers():
    """Transforma dados de clientes para a camada Silver."""
    delete_query = f"DELETE FROM `{project_id}.{silver_dataset}.clientes` WHERE TRUE"
    delete_job = bq_client.query(delete_query)
    delete_job.result()

    insert_query = f"""
        INSERT INTO `{project_id}.{silver_dataset}.clientes` (
            id_cliente,
            nome,
            email,
            telefone,
            endereco,
            cidade,
            estado,
            pais,
            data_cadastro,
            segmento_cliente,
            atualizado_em
        )
        SELECT
            id_cliente,
            nome,
            LOWER(email) as email,
            telefone,
            endereco,
            cidade,
            estado,
            pais,
            data_cadastro,
            segmento_cliente,
            CURRENT_TIMESTAMP() AS atualizado_em
        FROM `{project_id}.{bronze_dataset}.clientes`
        WHERE id_cliente IS NOT NULL
          AND nome IS NOT NULL
          AND email IS NOT NULL
    """
    insert_job = bq_client.query(insert_query)
    insert_job.result()


def transform_products():
    """Transforma dados de produtos para a camada Silver."""
    delete_query = f"DELETE FROM `{project_id}.{silver_dataset}.produtos` WHERE TRUE"
    delete_job = bq_client.query(delete_query)
    delete_job.result()

    insert_query = f"""
        INSERT INTO `{project_id}.{silver_dataset}.produtos` (
            id_produto,
            nome,
            categoria,
            subcategoria,
            preco,
            custo,
            quantidade_estoque,
            fornecedor,
            criado_em,
            margem_lucro,
            atualizado_em
        )
        SELECT
            id_produto,
            nome,
            categoria,
            subcategoria,
            preco,
            custo,
            quantidade_estoque,
            fornecedor,
            criado_em,
            CASE
                WHEN preco > 0 AND custo IS NOT NULL THEN ROUND((preco - custo) / preco, 4)
                ELSE NULL
            END as margem_lucro,
            CURRENT_TIMESTAMP() AS atualizado_em
        FROM `{project_id}.{bronze_dataset}.produtos`
        WHERE id_produto IS NOT NULL
          AND nome IS NOT NULL
          AND categoria IS NOT NULL
          AND preco > 0
    """
    insert_job = bq_client.query(insert_query)
    insert_job.result()


def transform_transactions():
    """Transforma dados de transações para a camada Silver."""
    delete_query = f"DELETE FROM `{project_id}.{silver_dataset}.transacoes` WHERE TRUE"
    delete_job = bq_client.query(delete_query)
    delete_job.result()

    insert_query = f"""
        INSERT INTO `{project_id}.{silver_dataset}.transacoes` (
            id_transacao,
            id_cliente,
            id_produto,
            quantidade,
            preco_unitario,
            valor_total,
            data_transacao,
            status,
            metodo_pagamento,
            atualizado_em
        )
        SELECT
            id_transacao,
            id_cliente,
            id_produto,
            quantidade,
            preco_unitario,
            valor_total,
            data_transacao,
            status,
            metodo_pagamento,
            CURRENT_TIMESTAMP() AS atualizado_em
        FROM `{project_id}.{bronze_dataset}.transacoes`
        WHERE id_transacao IS NOT NULL
          AND id_cliente IS NOT NULL
          AND id_produto IS NOT NULL
          AND quantidade > 0
          AND preco_unitario > 0
          AND valor_total > 0
    """
    insert_job = bq_client.query(insert_query)
    insert_job.result()
