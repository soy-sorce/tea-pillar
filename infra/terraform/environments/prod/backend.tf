terraform {
  backend "gcs" {
    bucket = "REPLACE_ME_TFSTATE_BUCKET"
    prefix = "terraform/prod"
  }
}
