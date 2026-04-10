provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  raw_bucket_name      = "${var.project_id}-pipeline-raw"
  bronze_topic_name    = "${var.project_id}-bronze-to-silver"
  analytics_topic_name = "${var.project_id}-silver-to-analytics"
  function_sa_id       = "pipeline-functions-sa"
  required_services = toset([
    "iam.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "pubsub.googleapis.com",
  ])
}

# Habilitar APIs necessárias no projeto
resource "google_project_service" "services" {
  for_each = local.required_services

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# Aguardar propagação das APIs antes de criar recursos
resource "time_sleep" "wait_for_apis" {
  depends_on      = [google_project_service.services]
  create_duration = "60s"
}

# Bucket para ingestão manual de dados
resource "google_storage_bucket" "raw" {
  name                        = local.raw_bucket_name
  location                    = var.location
  force_destroy               = false
  uniform_bucket_level_access = true
  depends_on                  = [time_sleep.wait_for_apis]
}

# Tópicos Pub/Sub para orquestração da pipeline
resource "google_pubsub_topic" "bronze_to_silver" {
  name       = local.bronze_topic_name
  depends_on = [time_sleep.wait_for_apis]
}

resource "google_pubsub_topic" "silver_to_analytics" {
  name       = local.analytics_topic_name
  depends_on = [time_sleep.wait_for_apis]
}

# Datasets BigQuery para as camadas da arquitetura Medallion
resource "google_bigquery_dataset" "bronze" {
  dataset_id  = "bronze"
  location    = var.location
  description = "Camada Bronze - dados de ingestão bruta"
  depends_on  = [time_sleep.wait_for_apis]
}

resource "google_bigquery_dataset" "silver" {
  dataset_id  = "silver"
  location    = var.location
  description = "Camada Silver - dados transformados e limpos"
  depends_on  = [time_sleep.wait_for_apis]
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id  = "analytics"
  location    = var.location
  description = "Camada Analytics - views para análise de dados"
  depends_on  = [time_sleep.wait_for_apis]
}

# Tabelas da camada Bronze
resource "google_bigquery_table" "bronze_customers" {
  dataset_id = google_bigquery_dataset.bronze.dataset_id
  table_id   = "clientes"

  schema = file("${path.module}/schemas/bronze_clientes.json")
}

resource "google_bigquery_table" "bronze_products" {
  dataset_id = google_bigquery_dataset.bronze.dataset_id
  table_id   = "produtos"

  schema = file("${path.module}/schemas/bronze_produtos.json")
}

resource "google_bigquery_table" "bronze_transactions" {
  dataset_id = google_bigquery_dataset.bronze.dataset_id
  table_id   = "transacoes"

  schema = file("${path.module}/schemas/bronze_transacoes.json")
}

# Tabelas da camada Silver
resource "google_bigquery_table" "silver_customers" {
  dataset_id = google_bigquery_dataset.silver.dataset_id
  table_id   = "clientes"

  schema = file("${path.module}/schemas/silver_clientes.json")
}

resource "google_bigquery_table" "silver_products" {
  dataset_id = google_bigquery_dataset.silver.dataset_id
  table_id   = "produtos"

  schema = file("${path.module}/schemas/silver_produtos.json")
}

resource "google_bigquery_table" "silver_transactions" {
  dataset_id = google_bigquery_dataset.silver.dataset_id
  table_id   = "transacoes"

  schema = file("${path.module}/schemas/silver_transacoes.json")
}

# Service Account para as Cloud Functions
resource "google_service_account" "functions" {
  account_id   = local.function_sa_id
  display_name = "Service Account para Pipeline Functions"
  depends_on   = [time_sleep.wait_for_apis]
}

# Permissões da Service Account
resource "google_project_iam_member" "functions_storage_read" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.functions.email}"
}

resource "google_project_iam_member" "functions_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.functions.email}"
}

resource "google_project_iam_member" "functions_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.functions.email}"
}

resource "google_project_iam_member" "functions_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.functions.email}"
}

resource "google_project_iam_member" "functions_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.functions.email}"
}
