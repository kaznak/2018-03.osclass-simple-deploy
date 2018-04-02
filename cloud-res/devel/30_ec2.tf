# EC2 -*- Mode: HCL; -*-

# Instance
# # https://www.terraform.io/docs/providers/aws/r/instance.html
resource "aws_instance" "osclass" {
  count = 1

  instance_type = "t2.micro"

  ami = "ami-25bd2743" # Original CentOS7 1801_01, release 2018-01-14
  # https://aws.amazon.com/marketplace/fulfillment?productId=b7ee8a69-ee97-4a49-9e68-afaee216db2e

  vpc_security_group_ids = [
    # "${aws_security_group.i_g_www.id}",
    "${aws_security_group.i_s_www.id}",

    "${aws_security_group.i_s_ssh.id}",
    "${aws_security_group.e_g_all.id}",
  ]
  subnet_id = "${aws_subnet.public.*.id[count.index % 3]}"
  key_name  = "${aws_key_pair.main.key_name}"
  # This instance does not require public ip address,
  # because EIP address will be associated to this instance.
  # but to work remote-exec provioner,
  # public address is required before finishing deployment of this instance
  # and after finishing deployment, EIP address will be associated.
  # Therefore public ip address association is required
  # while using remote-exec provisioner.
  associate_public_ip_address = true
  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = "centos"
      private_key = "${file("${local.ssh_dir}/id_rsa")}"
    }

    inline = [
      # # # Update System
      # "sudo yum -y update",
      # # Set hostname
      "sudo hostnamectl set-hostname osclass-${count.index}-$(date +%Y%m%dT%H%M%S)",
    ]
  }
  provisioner "local-exec" {
    when = "destroy"

    command = <<EOS
[ -s ${local.ssh_dir}/known_hosts ] &&
	rm -f ${local.ssh_dir}/known_hosts;true
EOS
  }
  tags = "${merge(
	map("Name","${var.ProjectName}_${count.index}"),
	"${local.common_tags}")}"
}

# # https://www.terraform.io/docs/providers/aws/r/key_pair.html
resource "aws_key_pair" "main" {
  key_name   = "${var.ProjectName}"
  public_key = "${file("${local.ssh_dir}/id_rsa.pub")}"
}

# # https://www.terraform.io/docs/providers/aws/r/eip.html
resource "aws_eip" "osclass" {
  vpc = true

  tags = "${merge(
	map("Name","${var.ProjectName}_${count.index}"),
	"${local.common_tags}")}"
}

# # https://www.terraform.io/docs/providers/aws/r/eip_association.html
resource "aws_eip_association" "osclass" {
  instance_id   = "${aws_instance.osclass.id}"
  allocation_id = "${aws_eip.osclass.id}"
}
