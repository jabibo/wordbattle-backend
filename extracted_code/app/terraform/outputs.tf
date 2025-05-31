output "app_runner_service_url" {
  description = "App Runner service URL"
  value       = "https://${aws_apprunner_service.main.service_url}"
}

output "app_runner_service_arn" {
  description = "App Runner service ARN"
  value       = aws_apprunner_service.main.arn
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.wordbattle.repository_url
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "database_username" {
  description = "Database username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "security_group_rds_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

output "security_group_app_runner_id" {
  description = "App Runner security group ID"
  value       = aws_security_group.app_runner.id
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.app_runner.name
}

output "ssm_parameter_db_password" {
  description = "SSM parameter name for database password"
  value       = aws_ssm_parameter.db_password.name
  sensitive   = true
}

output "ssm_parameter_secret_key" {
  description = "SSM parameter name for secret key"
  value       = aws_ssm_parameter.secret_key.name
  sensitive   = true
} 