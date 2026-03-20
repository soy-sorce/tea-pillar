output "frontend_service_account_email" {
  value = google_service_account.frontend.email
}

output "backend_service_account_email" {
  value = google_service_account.backend.email
}

output "apigateway_service_account_email" {
  value = google_service_account.apigateway.email
}
