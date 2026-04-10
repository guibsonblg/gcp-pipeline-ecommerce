variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "region" {
  description = "Região GCP para Cloud Functions e recursos"
  type        = string
  default     = "us-central1"
}

variable "location" {
  description = "Localização GCP para datasets BigQuery"
  type        = string
  default     = "US"
}
