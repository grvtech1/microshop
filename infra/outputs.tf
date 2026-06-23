output "master_ip" {
  value = aws_instance.master.public_ip
}

output "worker_ips" {
  value = aws_instance.worker[*].public_ip
}

output "rds_endpoint" {
  value = aws_db_instance.pg.address
}

output "ecr_urls" {
  value = { for k, r in aws_ecr_repository.repos : k => r.repository_url }
}
