data "google_project" "current" {
  project_id = var.project_id
}

resource "google_service_account" "frontend" {
  project      = var.project_id
  account_id   = "nekkoflix-frontend-sa-${var.environment}"
  display_name = "nekkoflix Frontend Service Account (${var.environment})"
}

resource "google_service_account" "backend" {
  project      = var.project_id
  account_id   = "nekkoflix-backend-sa-${var.environment}"
  display_name = "nekkoflix Backend Service Account (${var.environment})"
}

resource "google_service_account" "apigateway" {
  project      = var.project_id
  account_id   = "nekkoflix-apigw-sa-${var.environment}"
  display_name = "nekkoflix API Gateway Service Account (${var.environment})"
}

resource "google_cloud_run_v2_service_iam_member" "apigateway_invoke_backend" {
  location = var.region
  name     = var.backend_service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.apigateway.email}"
}

resource "google_project_iam_member" "backend_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_storage_bucket_iam_member" "backend_gcs_admin" {
  bucket = var.gcs_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "cloudbuild_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_run_deploy" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}
