output "artifact_registry_repository" {
  value = module.artifact_registry.repository_name
}

output "api_gateway_hostname" {
  value = module.api_gateway.gateway_default_hostname
}

output "gcs_bucket_name" {
  value = module.gcs.bucket_name
}

output "reaction_video_bucket_name" {
  value = module.reaction_video_gcs.bucket_name
}

output "firestore_database_id" {
  value = module.firestore.database_id
}

output "backend_service_account_email" {
  value = module.iam.backend_service_account_email
}

output "model_service_account_email" {
  value = module.iam.model_service_account_email
}

output "frontend_trigger_id" {
  value = module.frontend_trigger.trigger_id
}

output "backend_trigger_id" {
  value = module.backend_trigger.trigger_id
}

output "api_gateway_trigger_id" {
  value = module.api_gateway_trigger.trigger_id
}
