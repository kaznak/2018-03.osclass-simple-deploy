# Output -*- Mode: HCL; -*-
# # https://www.terraform.io/docs/configuration/outputs.html

output "ec2-addr" {
  value = "${aws_eip.osclass.public_ip}"
}
