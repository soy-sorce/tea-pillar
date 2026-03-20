terraform {
  required_version = ">= 1.7.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

locals {
  common_labels = {
    app         = "nekkoflix"
    environment = var.environment
    managed_by  = "terraform"
  }

  backend_env_vars = {
    ENVIRONMENT                      = var.environment
    LOG_LEVEL                        = var.backend_log_level
    GCP_PROJECT_ID                   = var.project_id
    GCP_REGION                       = var.region
    VERTEX_ENDPOINT_ID               = var.vertex_endpoint_resource_name
    VERTEX_ENDPOINT_LOCATION         = var.vertex_endpoint_location
    GCS_BUCKET_NAME                  = module.gcs.bucket_name
    GCS_SIGNED_URL_EXPIRATION_HOURS  = tostring(var.gcs_signed_url_expiration_hours)
    FIRESTORE_DATABASE_ID            = module.firestore.database_id
    GEMINI_MODEL                     = var.gemini_model
    GEMINI_TIMEOUT                   = tostring(var.gemini_timeout)
    VEO_MODEL                        = var.veo_model
    VEO_TIMEOUT                      = tostring(var.veo_timeout)
    VEO_POLLING_INTERVAL             = tostring(var.veo_polling_interval)
    BANDIT_UCB_ALPHA                 = tostring(var.bandit_ucb_alpha)
  }

  frontend_env_vars = {
    VITE_BACKEND_URL = var.frontend_backend_url_override != "" ? var.frontend_backend_url_override : module.api_gateway.gateway_default_hostname
  }
}

module "artifact_registry" {
  source        = "../../modules/artifact_registry"
  project_id    = var.project_id
  region        = var.region
  repository_id = var.artifact_registry_repository_id
  description   = "nekkoflix Docker images (${var.environment})"
  labels        = local.common_labels
}

module "firestore" {
  source      = "../../modules/firestore"
  project_id  = var.project_id
  region      = var.region
  database_id = var.firestore_database_id
  type        = "FIRESTORE_NATIVE"
}

module "gcs" {
  source             = "../../modules/gcs"
  project_id         = var.project_id
  region             = var.region
  bucket_name        = var.gcs_bucket_name
  environment        = var.environment
  lifecycle_age_days = var.gcs_lifecycle_age_days
  labels             = local.common_labels
}

module "vpc" {
  source                    = "../../modules/vpc"
  project_id                = var.project_id
  region                    = var.region
  environment               = var.environment
  network_name              = var.vpc_network_name
  subnet_name               = var.vpc_subnet_name
  subnet_cidr               = var.vpc_subnet_cidr
  connector_name            = var.vpc_connector_name
  connector_cidr            = var.vpc_connector_cidr
  connector_min_instances   = var.vpc_connector_min_instances
  connector_max_instances   = var.vpc_connector_max_instances
  connector_machine_type    = var.vpc_connector_machine_type
}

module "iam" {
  source                     = "../../modules/iam"
  project_id                 = var.project_id
  region                     = var.region
  environment                = var.environment
  backend_service_name       = var.backend_service_name
  frontend_service_name      = var.frontend_service_name
  api_gateway_service_name   = var.api_gateway_name
  gcs_bucket_name            = module.gcs.bucket_name
}

module "vertex_ai" {
  source                         = "../../modules/vertex_ai"
  project_id                     = var.project_id
  region                         = var.region
  endpoint_resource_name         = var.vertex_endpoint_resource_name
  endpoint_location              = var.vertex_endpoint_location
  backend_service_account_email  = module.iam.backend_service_account_email
  enable_vertex_api              = var.enable_vertex_api
}

module "backend_cloud_run" {
  source                 = "../../modules/cloud_run"
  project_id             = var.project_id
  region                 = var.region
  service_name           = var.backend_service_name
  image_uri              = var.backend_image_uri
  container_port         = 8080
  ingress                = var.backend_ingress
  min_instance_count     = var.backend_min_instances
  max_instance_count     = var.backend_max_instances
  timeout_seconds        = var.backend_timeout_seconds
  cpu                    = var.backend_cpu
  memory                 = var.backend_memory
  service_account_email  = module.iam.backend_service_account_email
  env_vars               = local.backend_env_vars
  labels                 = local.common_labels
  allow_unauthenticated  = false
  vpc_connector          = module.vpc.connector_id
  vpc_egress             = var.backend_vpc_egress
}

module "frontend_cloud_run" {
  source                 = "../../modules/cloud_run"
  project_id             = var.project_id
  region                 = var.region
  service_name           = var.frontend_service_name
  image_uri              = var.frontend_image_uri
  container_port         = 8080
  ingress                = var.frontend_ingress
  min_instance_count     = var.frontend_min_instances
  max_instance_count     = var.frontend_max_instances
  timeout_seconds        = var.frontend_timeout_seconds
  cpu                    = var.frontend_cpu
  memory                 = var.frontend_memory
  service_account_email  = module.iam.frontend_service_account_email
  env_vars               = local.frontend_env_vars
  labels                 = local.common_labels
  allow_unauthenticated  = true
}

module "api_gateway" {
  source                       = "../../modules/api_gateway"
  project_id                   = var.project_id
  region                       = var.region
  api_id                       = var.api_gateway_api_id
  api_config_id                = var.api_gateway_config_id
  gateway_id                   = var.api_gateway_name
  backend_url                  = module.backend_cloud_run.service_uri
  gateway_service_account_email = module.iam.apigateway_service_account_email
  openapi_template_path        = "${path.root}/../../../apigateway/openapi.yaml"
  jwt_issuer                   = var.api_gateway_jwt_issuer
  jwt_jwks_uri                 = var.api_gateway_jwt_jwks_uri
  jwt_audience                 = var.api_gateway_jwt_audience
}
