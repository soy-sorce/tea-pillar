resource "google_firestore_database" "this" {
  project                     = var.project_id
  name                        = var.database_id
  location_id                 = var.region
  type                        = var.type
  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
}
