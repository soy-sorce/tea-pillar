output "database_id" {
  value = google_firestore_database.this.name
}

output "location_id" {
  value = google_firestore_database.this.location_id
}
