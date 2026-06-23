variable "region" {
  default = "ap-south-1"
}

variable "my_ip" {
  description = "Tera public IP /32 (SSH allow karne ko). `curl ifconfig.me` se lo."
  type        = string
}

variable "db_password" {
  description = "RDS Postgres password"
  type        = string
  sensitive   = true
}

variable "worker_count" {
  description = "Kitne worker nodes (free-tier: 0 = single-node k3s)"
  default     = 0
}

variable "instance_type" {
  description = "EC2 type. Free-tier = t3.micro. Paid (real kubeadm) = t3.medium"
  default     = "t3.micro"
}

variable "public_key_path" {
  default = "~/.ssh/microshop.pub"
}
