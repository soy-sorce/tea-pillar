terraform {
  backend "gcs" {
    bucket = "gcp-hackathon-2026-tea-pillar-tfstate"
    prefix = "terraform/dev"
  }
}
