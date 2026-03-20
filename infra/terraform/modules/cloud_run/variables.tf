variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "service_name" {
  type = string
}

variable "image_uri" {
  type = string
}

variable "container_port" {
  type    = number
  default = 8080
}

variable "ingress" {
  type = string
}

variable "min_instance_count" {
  type = number
}

variable "max_instance_count" {
  type = number
}

variable "timeout_seconds" {
  type = number
}

variable "cpu" {
  type = string
}

variable "memory" {
  type = string
}

variable "service_account_email" {
  type = string
}

variable "env_vars" {
  type    = map(string)
  default = {}
}

variable "labels" {
  type    = map(string)
  default = {}
}

variable "allow_unauthenticated" {
  type    = bool
  default = false
}

variable "vpc_connector" {
  type    = string
  default = null
}

variable "vpc_egress" {
  type    = string
  default = "PRIVATE_RANGES_ONLY"
}
