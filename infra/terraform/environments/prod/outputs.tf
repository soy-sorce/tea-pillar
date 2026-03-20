output "artifact_registry_repository" {
  value = module.artifact_registry.repository_name
}

output "backend_service_uri" {
  value = module.backend_cloud_run.service_uri
}

output "frontend_service_uri" {
  value = module.frontend_cloud_run.service_uri
}

output "api_gateway_hostname" {
  value = module.api_gateway.gateway_default_hostname
}

output "gcs_bucket_name" {
  value = module.gcs.bucket_name
}

output "firestore_database_id" {
  value = module.firestore.database_id
}

output "backend_service_account_email" {
  value = module.iam.backend_service_account_email
}

output "vertex_endpoint_resource_name" {
  value = module.vertex_ai.endpoint_resource_name
}
