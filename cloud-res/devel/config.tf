# config -*- Mode: HCL; -*-

# Terraform Settings
# # https://www.terraform.io/docs/configuration/terraform.html
terraform {
  required_version = ">= 0.11.3"
}

# Provider
# # https://www.terraform.io/docs/providers/aws/index.html
provider "aws" {
  version = "~> 1.11"
  region  = "ap-northeast-1"

  profile = "sample-profile"
}

# Variables
# # https://www.terraform.io/docs/configuration/variables.html
variable "ProjectName" {
  type    = "string"
  default = "osclass-simple-deploy"

  # only lowercase alphanumeric characters and hyphens allowed
}

variable "Env" {
  type    = "string"
  default = "devel"
}

variable "Allow_Networks" {
  description = "Service Networks"
  type        = "list"

  default = [
    "0.0.0.0/0",
  ]
}
