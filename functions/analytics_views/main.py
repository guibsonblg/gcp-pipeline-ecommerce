import base64
import json
import os

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

project_id = os.environ.get("GCP_PROJECT_ID")
silver_dataset = os.environ.get("SILVER_DATASET", "silver")
analytics_dataset = os.environ.get("ANALYTICS_DATASET", "analytics")

bq_client = bigquery.Client()

VIEWS = {
    "resumo_clientes": f"""
        SELECT
            c.id_cliente,
            c.nome,
            c.email,
            c.cidade,
            c.estado,
            c.segmento_cliente,
            c.data_cadastro,
            COUNT(t.id_transacao) as total_transacoes,
            SUM(t.valor_total) as valor_total_gasto,
            AVG(t.valor_total) as valor_medio_transacao,
            MAX(t.data_transacao) as ultima_transacao,
            MIN(t.data_transacao) as primeira_transacao
        FROM `{project_id}.{silver_dataset}.clientes` c
        LEFT JOIN `{project_id}.{silver_dataset}.transacoes` t
            ON c.id_cliente = t.id_cliente
            AND t.status = 'completed'
        GROUP BY c.id_cliente, c.nome, c.email, c.cidade, c.estado, c.segmento_cliente, c.data_cadastro
    """,
    "performance_produtos": f"""
        SELECT
            p.id_produto,
            p.nome,
            p.categoria,
            p.subcategoria,
            p.preco,
            p.custo,
            p.margem_lucro,
            p.quantidade_estoque,
            p.fornecedor,
            COUNT(t.id_transacao) as total_vendas,
            SUM(t.quantidade) as quantidade_vendida,
            SUM(t.valor_total) as receita_total,
            AVG(t.preco_unitario) as preco_medio_vendido,
            MAX(t.data_transacao) as ultima_venda
        FROM `{project_id}.{silver_dataset}.produtos` p
        LEFT JOIN `{project_id}.{silver_dataset}.transacoes` t
            ON p.id_produto = t.id_produto
            AND t.status = 'completed'
        GROUP BY p.id_produto, p.nome, p.categoria, p.subcategoria, p.preco, p.custo, p.margem_lucro, p.quantidade_estoque, p.fornecedor
    """,
    "vendas_por_categoria": f"""
        SELECT
            p.categoria,
            p.subcategoria,
            COUNT(DISTINCT t.id_transacao) as total_transacoes,
            SUM(t.quantidade) as quantidade_total_vendida,
            SUM(t.valor_total) as receita_total,
            AVG(t.valor_total) as valor_medio_transacao,
            COUNT(DISTINCT t.id_cliente) as clientes_unicos
        FROM `{project_id}.{silver_dataset}.transacoes` t
        JOIN `{project_id}.{silver_dataset}.produtos` p
            ON t.id_produto = p.id_produto
        WHERE t.status = 'completed'
        GROUP BY p.categoria, p.subcategoria
    """,
    "vendas_diarias": f"""
        SELECT
            DATE(t.data_transacao) as data_venda,
            COUNT(DISTINCT t.id_transacao) as total_transacoes,
            COUNT(DISTINCT t.id_cliente) as clientes_unicos,
            SUM(t.valor_total) as receita_total,
            SUM(t.quantidade) as itens_totais_vendidos,
            AVG(t.valor_total) as valor_medio_transacao
        FROM `{project_id}.{silver_dataset}.transacoes` t
        WHERE t.status = 'completed'
        GROUP BY DATE(t.data_transacao)
    """,
    "valor_vida_cliente": f"""
        SELECT
            c.id_cliente,
            c.nome,
            c.segmento_cliente,
            c.data_cadastro,
            COUNT(t.id_transacao) as numero_transacoes,
            SUM(t.valor_total) as valor_vida,
            AVG(t.valor_total) as valor_medio_pedido,
            MAX(t.data_transacao) as ultima_compra,
            DATE_DIFF(CURRENT_DATE(), DATE(c.data_cadastro), DAY) as dias_desde_cadastro,
            DATE_DIFF(CURRENT_DATE(), DATE(MAX(t.data_transacao)), DAY) as dias_desde_ultima_compra,
            CASE
                WHEN COUNT(t.id_transacao) > 10 THEN 'Alto Valor'
                WHEN COUNT(t.id_transacao) > 5 THEN 'Valor Médio'
                WHEN COUNT(t.id_transacao) > 0 THEN 'Baixo Valor'
                ELSE 'Sem Compras'
            END as segmento_valor_cliente
        FROM `{project_id}.{silver_dataset}.clientes` c
        LEFT JOIN `{project_id}.{silver_dataset}.transacoes` t
            ON c.id_cliente = t.id_cliente
            AND t.status = 'completed'
        GROUP BY c.id_cliente, c.nome, c.segmento_cliente, c.data_cadastro
    """,
    "status_inventario": f"""
        SELECT
            p.id_produto,
            p.nome,
            p.categoria,
            p.quantidade_estoque,
            p.fornecedor,
            CASE
                WHEN p.quantidade_estoque = 0 THEN 'Esgotado'
                WHEN p.quantidade_estoque <= 10 THEN 'Estoque Baixo'
                WHEN p.quantidade_estoque <= 50 THEN 'Estoque Médio'
                ELSE 'Bem Estoqueado'
            END as status_estoque,
            SUM(t.quantidade) as vendido_ultimos_30_dias
        FROM `{project_id}.{silver_dataset}.produtos` p
        LEFT JOIN `{project_id}.{silver_dataset}.transacoes` t
            ON p.id_produto = t.id_produto
            AND t.status = 'completed'
            AND DATE(t.data_transacao) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY p.id_produto, p.nome, p.categoria, p.quantidade_estoque, p.fornecedor
    """
}


def create_analytics_views(event, context):
    """Cria/atualiza views analíticas no dataset Analytics."""
    payload = {}
    if event.get("data"):
        payload = json.loads(base64.b64decode(event["data"]).decode("utf-8"))

    for view_id, query in VIEWS.items():
        view_ref = bigquery.Table(f"{project_id}.{analytics_dataset}.{view_id}")
        view_ref.view_query = query

        try:
            existing = bq_client.get_table(view_ref)
            existing.view_query = query
            bq_client.update_table(existing, ["view_query"])
        except NotFound:
            bq_client.create_table(view_ref)

    return {
        "status": "sucesso",
        "views": list(VIEWS.keys()),
        "payload": payload,
    }
