variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

variable "description" {
  type    = string
  default = ""
}

variable "filename" {
  type = string
}

variable "github_owner" {
  type = string
}

variable "github_name" {
  type = string
}

variable "branch_regex" {
  type    = string
  default = "^main$"
}

variable "included_files" {
  type    = list(string)
  default = []
}

variable "ignored_files" {
  type    = list(string)
  default = []
}

variable "substitutions" {
  type    = map(string)
  default = {}
}

variable "enabled" {
  type    = bool
  default = true
}
