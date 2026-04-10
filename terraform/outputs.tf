output "raw_bucket_name" {
  description = "Bucket GCS para ingestão manual"
  value       = google_storage_bucket.raw.name
}

output "bronze_to_silver_topic" {
  description = "Tópico Pub/Sub para eventos Bronze → Silver"
  value       = google_pubsub_topic.bronze_to_silver.name
}

output "silver_to_analytics_topic" {
  description = "Tópico Pub/Sub para eventos Silver → Analytics"
  value       = google_pubsub_topic.silver_to_analytics.name
}

output "functions_service_account" {
  description = "Service account usada pelas Cloud Functions"
  value       = google_service_account.functions.email
}
