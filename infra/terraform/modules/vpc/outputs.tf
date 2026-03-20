output "network_id" {
  value = google_compute_network.this.id
}

output "subnet_id" {
  value = google_compute_subnetwork.this.id
}

output "connector_id" {
  value = google_vpc_access_connector.this.id
}
