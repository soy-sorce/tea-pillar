variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "database_id" {
  type    = string
  default = "(default)"
}

variable "type" {
  type    = string
  default = "FIRESTORE_NATIVE"
}
