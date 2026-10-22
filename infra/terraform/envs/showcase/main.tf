terraform {
  required_version = ">= 1.6.0"
}

module "storage" {
  count  = var.enable_storage ? 1 : 0
  source = "../../modules/storage"

  project_name             = var.project_name
  github_actions_role_name = var.github_actions_role_name
}
