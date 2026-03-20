variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "repository_id" {
  type = string
}

variable "description" {
  type    = string
  default = "Docker repository"
}

variable "labels" {
  type    = map(string)
  default = {}
}
