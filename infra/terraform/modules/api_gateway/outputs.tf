output "gateway_default_hostname" {
  value = "https://${google_api_gateway_gateway.this.default_hostname}"
}

output "gateway_id" {
  value = google_api_gateway_gateway.this.gateway_id
}
