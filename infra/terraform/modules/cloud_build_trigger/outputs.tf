output "trigger_id" {
  value = var.enabled ? google_cloudbuild_trigger.this[0].trigger_id : null
}

output "name" {
  value = var.enabled ? google_cloudbuild_trigger.this[0].name : null
}
