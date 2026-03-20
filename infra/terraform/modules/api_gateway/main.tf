terraform {
  required_providers {
    google-beta = {
      source = "hashicorp/google-beta"
    }
  }
}

resource "google_project_service" "apigateway" {
  project            = var.project_id
  service            = "apigateway.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "servicemanagement" {
  project            = var.project_id
  service            = "servicemanagement.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "servicecontrol" {
  project            = var.project_id
  service            = "servicecontrol.googleapis.com"
  disable_on_destroy = false
}

locals {
  openapi_rendered = templatefile(var.openapi_template_path, {
    backend_url  = var.backend_url
    jwt_issuer   = var.jwt_issuer
    jwt_jwks_uri = var.jwt_jwks_uri
    jwt_audience = var.jwt_audience
  })
}

resource "google_api_gateway_api" "this" {
  provider = google-beta
  project  = var.project_id
  api_id   = var.api_id

  depends_on = [
    google_project_service.apigateway,
    google_project_service.servicemanagement,
    google_project_service.servicecontrol,
  ]
}

resource "google_api_gateway_api_config" "this" {
  provider      = google-beta
  project       = var.project_id
  api           = google_api_gateway_api.this.api_id
  api_config_id = var.api_config_id

  openapi_documents {
    document {
      path     = "openapi.yaml"
      contents = base64encode(local.openapi_rendered)
    }
  }

  gateway_config {
    backend_config {
      google_service_account = var.gateway_service_account_email
    }
  }

  depends_on = [
    google_project_service.apigateway,
    google_project_service.servicemanagement,
    google_project_service.servicecontrol,
  ]
}

resource "google_api_gateway_gateway" "this" {
  provider   = google-beta
  project    = var.project_id
  region     = var.region
  gateway_id = var.gateway_id
  api_config = google_api_gateway_api_config.this.id
}
