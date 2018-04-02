# Network -*- Mode: HCL; -*-

# Variables
# # https://www.terraform.io/docs/configuration/variables.html
variable "VPC_CIDR_Block" {
  type    = "string"
  default = "10.0.0.0/16"
}

variable "public_CIDR_Blocks" {
  type = "map"

  default = {
    "0" = "10.0.1.0/24"
    "1" = "10.0.2.0/24"
    "2" = "10.0.3.0/24"
  }
}

# VPC
# # https://www.terraform.io/docs/providers/aws/r/vpc.html
resource "aws_vpc" "main" {
  cidr_block = "${var.VPC_CIDR_Block}"

  tags = "${merge(
	map("Name","${var.ProjectName}"),
	"${local.common_tags}")}"
}

# # https://www.terraform.io/docs/providers/aws/r/internet_gateway.html
resource "aws_internet_gateway" "main" {
  vpc_id = "${aws_vpc.main.id}"

  tags = "${merge(
	map("Name","${var.ProjectName}"),
	"${local.common_tags}")}"
}

# # https://www.terraform.io/docs/providers/aws/r/route_table.html
resource "aws_route_table" "main" {
  vpc_id = "${aws_vpc.main.id}"

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.main.id}"
  }

  tags = "${merge(
	map("Name","${var.ProjectName}"),
	"${local.common_tags}")}"
}

# # https://www.terraform.io/docs/providers/aws/r/main_route_table_assoc.html
resource "aws_main_route_table_association" "main" {
  vpc_id         = "${aws_vpc.main.id}"
  route_table_id = "${aws_route_table.main.id}"
}

# ACL
# # https://www.terraform.io/docs/providers/aws/r/network_acl.html
resource "aws_network_acl" "public" {
  vpc_id = "${aws_vpc.main.id}"

  subnet_ids = [
    "${aws_subnet.public.*.id}",
  ]

  ingress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "${var.VPC_CIDR_Block}"
    from_port  = 0
    to_port    = 0
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 200
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 300
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 400
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 22
    to_port    = 22
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 910
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024

    # from_port  = 49152
    to_port = 65535
  }

  ingress {
    protocol   = "udp"
    rule_no    = 920
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024

    # from_port  = 49152
    to_port = 65535
  }

  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = "${merge(
	map("Name","${var.ProjectName}_Public"),
	"${local.common_tags}")}"
}

# Subnet
# # https://www.terraform.io/docs/providers/aws/r/subnet.html
resource "aws_subnet" "public" {
  count = 1

  vpc_id            = "${aws_vpc.main.id}"
  cidr_block        = "${lookup(var.public_CIDR_Blocks, count.index)}"
  availability_zone = "${lookup(var.AZ, count.index)}"

  tags = "${merge(
	map("Name","${var.ProjectName}_Public_${count.index}"),
	"${local.common_tags}")}"
}

## Security Groups
## # https://www.terraform.io/docs/providers/aws/r/security_group.html
resource "aws_security_group" "i_g_all" {
  name   = "${var.ProjectName}_i_g_all"
  vpc_id = "${aws_vpc.main.id}"

  ingress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = "${merge(
	map("Name","${var.ProjectName}_i_g_all"),
	"${local.common_tags}")}"
}

resource "aws_security_group" "e_g_all" {
  name   = "${var.ProjectName}_e_g_all"
  vpc_id = "${aws_vpc.main.id}"

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = "${merge(
	map("Name","${var.ProjectName}_e_g_all"),
	"${local.common_tags}")}"
}

resource "aws_security_group" "i_g_www" {
  name   = "${var.ProjectName}_i_g_www"
  vpc_id = "${aws_vpc.main.id}"

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = "${merge(
	map("Name","${var.ProjectName}_i_g_www"),
	"${local.common_tags}")}"
}

resource "aws_security_group" "i_s_www" {
  name   = "${var.ProjectName}_i_s_www"
  vpc_id = "${aws_vpc.main.id}"

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = "${var.Allow_Networks}"
  }

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = "${var.Allow_Networks}"
  }

  tags = "${merge(
	map("Name","${var.ProjectName}_i_s_www"),
	"${local.common_tags}")}"
}

resource "aws_security_group" "i_s_ssh" {
  name   = "${var.ProjectName}_i_s_ssh"
  vpc_id = "${aws_vpc.main.id}"

  ingress {
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = "${var.Allow_Networks}"
  }

  tags = "${merge(
	map("Name","${var.ProjectName}_i_s_ssh"),
	"${local.common_tags}")}"
}
