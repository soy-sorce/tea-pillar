variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "endpoint_resource_name" {
  type = string
}

variable "endpoint_location" {
  type = string
}

variable "backend_service_account_email" {
  type = string
}

variable "enable_vertex_api" {
  type    = bool
  default = true
}
