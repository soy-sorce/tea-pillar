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
    origin          = ["*"]
    method          = ["GET"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }
}
