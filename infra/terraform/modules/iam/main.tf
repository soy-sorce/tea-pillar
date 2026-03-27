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

resource "google_service_account" "model" {
  project      = var.project_id
  account_id   = "nekkoflix-model-sa-${var.environment}"
  display_name = "nekkoflix Model Service Account (${var.environment})"
}

resource "google_service_account" "apigateway" {
  project      = var.project_id
  account_id   = "nekkoflix-apigw-sa-${var.environment}"
  display_name = "nekkoflix API Gateway Service Account (${var.environment})"
}

resource "google_project_iam_member" "backend_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_service_account_iam_member" "backend_sign_blob_self" {
  service_account_id = google_service_account.backend.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_storage_bucket_iam_member" "backend_gcs_admin" {
  bucket = var.gcs_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_storage_bucket_iam_member" "backend_reaction_video_admin" {
  bucket = var.reaction_video_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_storage_bucket_iam_member" "model_gcs_viewer" {
  bucket = var.gcs_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.model.email}"
}

resource "google_storage_bucket_iam_member" "model_reaction_video_viewer" {
  bucket = var.reaction_video_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.model.email}"
}

resource "google_cloud_run_v2_service_iam_member" "model_invoker_by_backend" {
  project  = var.project_id
  location = var.region
  name     = var.model_service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_cloud_run_v2_service_iam_member" "backend_invoker_by_apigateway" {
  project  = var.project_id
  location = var.region
  name     = var.backend_service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.apigateway.email}"
}

resource "google_project_iam_member" "backend_vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "cloudbuild_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_api_gateway_admin" {
  project = var.project_id
  role    = "roles/apigateway.admin"
  member  = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}
