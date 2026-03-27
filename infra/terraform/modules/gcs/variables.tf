variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "lifecycle_age_days" {
  type    = number
  default = 1
}

variable "labels" {
  type    = map(string)
  default = {}
}

variable "cors_origins" {
  type = list(string)
}

variable "cors_methods" {
  type = list(string)
}

variable "cors_response_headers" {
  type    = list(string)
  default = ["Content-Type"]
}

variable "cors_max_age_seconds" {
  type    = number
  default = 3600
}
