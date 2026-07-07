# Configure HCP Terraform (Terraform Cloud) remote state.
# Replace organization and workspace before apply.
terraform {
  cloud {
    organization = "YOUR_HCP_ORG"
    workspaces {
      name = "mlops-showcase"
    }
  }
}

# Local backend for validation without HCP (comment cloud block above):
# terraform {
#   backend "local" {
#     path = "terraform.tfstate"
#   }
# }
