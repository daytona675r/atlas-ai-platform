variable "project_name" {
  type    = string
  default = "mlops-showcase"
}

variable "enable_storage" {
  type    = bool
  default = false
}

variable "github_actions_role_name" {
  type    = string
  default = ""
}
