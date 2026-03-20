variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-northeast1"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "artifact_registry_repository_id" {
  type    = string
  default = "nekkoflix"
}

variable "gcs_bucket_name" {
  type = string
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

variable "api_gateway_name" {
  type = string
}

variable "api_gateway_api_id" {
  type = string
}

variable "api_gateway_config_id" {
  type = string
}

variable "frontend_image_uri" {
  type = string
}

variable "backend_image_uri" {
  type = string
}

variable "vertex_endpoint_resource_name" {
  type = string
}

variable "vertex_endpoint_location" {
  type    = string
  default = "asia-northeast1"
}

variable "enable_vertex_api" {
  type    = bool
  default = true
}

variable "frontend_backend_url_override" {
  type    = string
  default = ""
}

variable "frontend_min_instances" {
  type    = number
  default = 0
}

variable "frontend_max_instances" {
  type    = number
  default = 3
}

variable "frontend_timeout_seconds" {
  type    = number
  default = 60
}

variable "frontend_cpu" {
  type    = string
  default = "1"
}

variable "frontend_memory" {
  type    = string
  default = "512Mi"
}

variable "frontend_ingress" {
  type    = string
  default = "INGRESS_TRAFFIC_ALL"
}

variable "backend_min_instances" {
  type    = number
  default = 1
}

variable "backend_max_instances" {
  type    = number
  default = 5
}

variable "backend_timeout_seconds" {
  type    = number
  default = 360
}

variable "backend_cpu" {
  type    = string
  default = "1"
}

variable "backend_memory" {
  type    = string
  default = "1Gi"
}

variable "backend_ingress" {
  type    = string
  default = "INGRESS_TRAFFIC_INTERNAL_ONLY"
}

variable "backend_vpc_egress" {
  type    = string
  default = "PRIVATE_RANGES_ONLY"
}

variable "backend_log_level" {
  type    = string
  default = "INFO"
}

variable "gemini_model" {
  type    = string
  default = "gemini-1.5-flash"
}

variable "gemini_timeout" {
  type    = number
  default = 15
}

variable "veo_model" {
  type    = string
  default = "veo-3.1-fast"
}

variable "veo_timeout" {
  type    = number
  default = 300
}

variable "veo_polling_interval" {
  type    = number
  default = 5
}

variable "bandit_ucb_alpha" {
  type    = number
  default = 1.0
}

variable "vpc_network_name" {
  type    = string
  default = "nekkoflix-vpc-prod"
}

variable "vpc_subnet_name" {
  type    = string
  default = "nekkoflix-backend-subnet-prod"
}

variable "vpc_subnet_cidr" {
  type    = string
  default = "10.0.0.0/24"
}

variable "vpc_connector_name" {
  type    = string
  default = "nkfx-vpcconn-prod"
}

variable "vpc_connector_cidr" {
  type    = string
  default = "10.8.0.0/28"
}

variable "vpc_connector_min_instances" {
  type    = number
  default = 2
}

variable "vpc_connector_max_instances" {
  type    = number
  default = 3
}

variable "vpc_connector_machine_type" {
  type    = string
  default = "e2-micro"
}

variable "api_gateway_jwt_issuer" {
  type = string
}

variable "api_gateway_jwt_jwks_uri" {
  type = string
}

variable "api_gateway_jwt_audience" {
  type = string
}
