terraform {
  backend "gcs" {
    bucket = "gdgoc-hackathon-2026-491600-tea-pillar-tfstate"
    prefix = "terraform/prod"
  }
}
