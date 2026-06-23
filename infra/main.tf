terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region
}

# ---- Ubuntu 22.04 AMI (latest, auto-fetch — hardcode nahi) ----
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# ---- Networking ----
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = "microshop-vpc" }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.region}a"
  map_public_ip_on_launch = true
  tags                    = { Name = "microshop-public-a" }
}

resource "aws_subnet" "public_b" { # RDS ko 2 AZ chahiye (HA)
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.region}b"
  tags              = { Name = "microshop-public-b" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "microshop-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

# ---- Security Group (firewall) ----
resource "aws_security_group" "k8s" {
  name   = "microshop-sg"
  vpc_id = aws_vpc.main.id

  ingress { # SSH — sirf tera IP
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress { # k8s API
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  ingress { # NodePort range
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress { # internal — pods/nodes aapas mein (self)
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "microshop-sg" }
}

# ---- SSH key ----
resource "aws_key_pair" "k" {
  key_name   = "microshop"
  public_key = file(var.public_key_path)
}

# ---- EC2: 1 master + N workers ----
resource "aws_instance" "master" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public_a.id
  key_name               = aws_key_pair.k.key_name
  vpc_security_group_ids = [aws_security_group.k8s.id]
  tags                   = { Name = "microshop-master" }
}

resource "aws_instance" "worker" {
  count                  = var.worker_count
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public_a.id
  key_name               = aws_key_pair.k.key_name
  vpc_security_group_ids = [aws_security_group.k8s.id]
  tags                   = { Name = "microshop-worker-${count.index}" }
}

# ---- RDS Postgres (stateful, managed) ----
resource "aws_db_subnet_group" "db" {
  name       = "microshop-db"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_db_instance" "pg" {
  identifier             = "microshop-pg"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "microshop"
  username               = "appuser"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.k8s.id]
  skip_final_snapshot    = true # lab — prod mein false!
  publicly_accessible    = false
}

# ---- ECR: 3 repos (per service) ----
resource "aws_ecr_repository" "repos" {
  for_each = toset(["catalog-api", "order-api", "frontend"])
  name     = "microshop/${each.key}"
}
