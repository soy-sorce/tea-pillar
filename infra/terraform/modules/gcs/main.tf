resource "google_storage_bucket" "this" {
  name          = var.bucket_name
  project       = var.project_id
  location      = var.region
  force_destroy = var.environment != "prod"

  public_access_prevention    = "enforced"
  uniform_bucket_level_access = true
  labels                      = var.labels

  lifecycle_rule {
    condition {
      age = var.lifecycle_age_days
    }
    action {
      type = "Delete"
    }
  }

  cors {
    origin          = var.cors_origins
    method          = var.cors_methods
    response_header = var.cors_response_headers
    max_age_seconds = var.cors_max_age_seconds
  }
}
