# Variables  -*- Mode: HCL; -*-

# # https://www.terraform.io/docs/configuration/variables.html
variable "AZ" {
  type = "map"

  default = {
    "0" = "ap-northeast-1a"
    "1" = "ap-northeast-1c"
    "2" = "ap-northeast-1d"
  }
}

locals {
  common_tags = {
    Project   = "${var.ProjectName}"
    Env       = "${var.Env}"
    Terraform = "true"
  }

  ssh_dir = "${path.module}/../../dot_ssh"
}
