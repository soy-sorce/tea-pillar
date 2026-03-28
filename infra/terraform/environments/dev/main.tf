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
  cors_origins       = [var.backend_frontend_origin]
  cors_methods       = ["GET"]
}

module "reaction_video_gcs" {
  source             = "../../modules/gcs"
  project_id         = var.project_id
  region             = var.region
  bucket_name        = var.reaction_video_bucket_name
  environment        = var.environment
  lifecycle_age_days = var.gcs_lifecycle_age_days
  labels             = local.common_labels
  cors_origins       = [var.backend_frontend_origin]
  cors_methods       = ["PUT"]
}

module "iam" {
  source                     = "../../modules/iam"
  project_id                 = var.project_id
  region                     = var.region
  environment                = var.environment
  gcs_bucket_name            = module.gcs.bucket_name
  reaction_video_bucket_name = module.reaction_video_gcs.bucket_name
}

module "api_gateway" {
  source                        = "../../modules/api_gateway"
  project_id                    = var.project_id
  region                        = var.region
  api_id                        = var.api_gateway_api_id
  api_config_id                 = var.api_gateway_config_id
  gateway_id                    = var.api_gateway_name
  backend_url                   = var.backend_url
  gateway_service_account_email = module.iam.apigateway_service_account_email
  openapi_template_path         = "${path.root}/../../../apigateway/openapi.yaml"
}

module "frontend_trigger" {
  source       = "../../modules/cloud_build_trigger"
  project_id   = var.project_id
  enabled      = var.enable_cloud_build_triggers
  name         = var.frontend_trigger_name
  description  = "Deploy frontend on main branch push"
  filename     = "infra/ci/cloud_build/cloudbuild-frontend.yaml"
  github_owner = var.github_owner
  github_name  = var.github_repo_name
  branch_regex = var.trigger_branch_regex
  included_files = [
    "frontend/**",
    "infra/ci/cloud_build/cloudbuild-frontend.yaml",
  ]
  substitutions = {
    _REGION           = var.region
    _REPOSITORY       = var.artifact_registry_repository_id
    _SERVICE_NAME     = var.frontend_service_name
    _SERVICE_ACCOUNT  = module.iam.frontend_service_account_email
    _VITE_BACKEND_URL = var.frontend_backend_url_override != "" ? var.frontend_backend_url_override : "https://${module.api_gateway.gateway_default_hostname}"
  }
}

module "backend_trigger" {
  source       = "../../modules/cloud_build_trigger"
  project_id   = var.project_id
  enabled      = var.enable_cloud_build_triggers
  name         = var.backend_trigger_name
  description  = "Deploy backend on main branch push"
  filename     = "infra/ci/cloud_build/cloudbuild-backend.yaml"
  github_owner = var.github_owner
  github_name  = var.github_repo_name
  branch_regex = var.trigger_branch_regex
  included_files = [
    "backend/**",
    "infra/ci/cloud_build/cloudbuild-backend.yaml",
  ]
  substitutions = {
    _REGION                                    = var.region
    _REPOSITORY                                = var.artifact_registry_repository_id
    _SERVICE_NAME                              = var.backend_service_name
    _SERVICE_ACCOUNT                           = module.iam.backend_service_account_email
    _MODEL_SERVICE_URL                         = var.model_service_url
    _GCS_BUCKET_NAME                           = module.gcs.bucket_name
    _REACTION_VIDEO_BUCKET_NAME                = module.reaction_video_gcs.bucket_name
    _FIRESTORE_DATABASE_ID                     = var.firestore_database_id
    _FRONTEND_ORIGIN                           = var.backend_frontend_origin
    _ENVIRONMENT                               = var.environment
    _LOG_LEVEL                                 = var.backend_log_level
    _GCS_SIGNED_URL_EXPIRATION_HOURS           = tostring(var.gcs_signed_url_expiration_hours)
    _REACTION_VIDEO_UPLOAD_URL_EXPIRES_SECONDS = tostring(var.reaction_video_upload_url_expires_seconds)
  }
}

module "model_trigger" {
  source       = "../../modules/cloud_build_trigger"
  project_id   = var.project_id
  enabled      = var.enable_cloud_build_triggers
  name         = var.model_trigger_name
  description  = "Deploy model on main branch push"
  filename     = "infra/ci/cloud_build/cloudbuild-model.yaml"
  github_owner = var.github_owner
  github_name  = var.github_repo_name
  branch_regex = var.trigger_branch_regex
  included_files = [
    "model/**",
    "infra/ci/cloud_build/cloudbuild-model.yaml",
  ]
  substitutions = {
    _REGION                  = var.region
    _REPOSITORY              = var.artifact_registry_repository_id
    _SERVICE_NAME            = var.model_service_name
    _IMAGE_NAME              = var.model_service_name
    _SERVICE_ACCOUNT         = module.iam.model_service_account_email
    _BACKEND_SERVICE_ACCOUNT = module.iam.backend_service_account_email
  }
}

module "api_gateway_trigger" {
  source       = "../../modules/cloud_build_trigger"
  project_id   = var.project_id
  enabled      = var.enable_cloud_build_triggers
  name         = var.api_gateway_trigger_name
  description  = "Deploy API Gateway config on main branch push"
  filename     = "infra/ci/cloud_build/cloudbuild-apigateway.yaml"
  github_owner = var.github_owner
  github_name  = var.github_repo_name
  branch_regex = var.trigger_branch_regex
  included_files = [
    "infra/apigateway/openapi.yaml",
    "infra/ci/cloud_build/cloudbuild-apigateway.yaml",
  ]
  substitutions = {
    _REGION                  = var.region
    _API_ID                  = var.api_gateway_api_id
    _API_CONFIG_ID           = var.api_gateway_config_id
    _GATEWAY_ID              = var.api_gateway_name
    _BACKEND_URL             = var.backend_url
    _GATEWAY_SERVICE_ACCOUNT = module.iam.apigateway_service_account_email
  }
}
