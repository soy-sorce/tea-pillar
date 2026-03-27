variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-northeast1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "artifact_registry_repository_id" {
  type    = string
  default = "nekkoflix"
}

variable "gcs_bucket_name" {
  type = string
}

variable "reaction_video_bucket_name" {
  type = string
}

variable "reaction_video_upload_url_expires_seconds" {
  type    = number
  default = 900
}

variable "gcs_lifecycle_age_days" {
  type    = number
  default = 1
}

variable "gcs_signed_url_expiration_hours" {
  type    = number
  default = 1
}

variable "firestore_database_id" {
  type    = string
  default = "(default)"
}

variable "frontend_service_name" {
  type = string
}

variable "backend_service_name" {
  type = string
}

variable "model_service_name" {
  type = string
}

variable "api_gateway_name" {
  type = string
}

variable "api_gateway_api_id" {
  type = string
}

variable "api_gateway_config_id" {
  type = string
}

variable "backend_url" {
  type = string
}

variable "model_service_url" {
  type = string
}

variable "frontend_backend_url_override" {
  type    = string
  default = ""
}

variable "backend_frontend_origin" {
  type = string
}

variable "backend_log_level" {
  type    = string
  default = "INFO"
}

variable "github_owner" {
  type = string
}

variable "github_repo_name" {
  type = string
}

variable "trigger_branch_regex" {
  type    = string
  default = "^main$"
}

variable "frontend_trigger_name" {
  type    = string
  default = "nekkoflix-frontend-trigger-dev"
}

variable "backend_trigger_name" {
  type    = string
  default = "nekkoflix-backend-trigger-dev"
}

variable "model_trigger_name" {
  type    = string
  default = "nekkoflix-model-trigger-dev"
}

variable "api_gateway_trigger_name" {
  type    = string
  default = "nekkoflix-apigateway-trigger-dev"
}
