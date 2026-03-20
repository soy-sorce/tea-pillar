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
