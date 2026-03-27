resource "google_project_service" "cloudbuild" {
  project            = var.project_id
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_cloudbuild_trigger" "this" {
  project     = var.project_id
  name        = var.name
  description = var.description
  filename    = var.filename

  github {
    owner = var.github_owner
    name  = var.github_name

    push {
      branch = var.branch_regex
    }
  }

  included_files = var.included_files
  ignored_files  = var.ignored_files

  substitutions = var.substitutions

  depends_on = [google_project_service.cloudbuild]
}
