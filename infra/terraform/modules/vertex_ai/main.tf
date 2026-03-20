resource "google_project_service" "aiplatform" {
  count              = var.enable_vertex_api ? 1 : 0
  project            = var.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_iam_member" "backend_vertex_endpoint_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${var.backend_service_account_email}"
}
