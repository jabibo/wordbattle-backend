variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "wordbattle"
}

# Database variables
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS instance (GB)"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS instance (GB)"
  type        = number
  default     = 100
}

variable "db_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

# App Runner variables
variable "app_runner_cpu" {
  description = "App Runner CPU configuration"
  type        = string
  default     = "0.25 vCPU"
  
  validation {
    condition = contains([
      "0.25 vCPU",
      "0.5 vCPU",
      "1 vCPU",
      "2 vCPU",
      "4 vCPU"
    ], var.app_runner_cpu)
    error_message = "App Runner CPU must be one of: 0.25 vCPU, 0.5 vCPU, 1 vCPU, 2 vCPU, 4 vCPU."
  }
}

variable "app_runner_memory" {
  description = "App Runner memory configuration"
  type        = string
  default     = "0.5 GB"
  
  validation {
    condition = contains([
      "0.5 GB",
      "1 GB",
      "2 GB",
      "3 GB",
      "4 GB",
      "6 GB",
      "8 GB",
      "10 GB",
      "12 GB"
    ], var.app_runner_memory)
    error_message = "App Runner memory must be a valid configuration."
  }
}

variable "auto_deployments_enabled" {
  description = "Enable automatic deployments for App Runner"
  type        = bool
  default     = true
}

# Email configuration
variable "smtp_server" {
  description = "SMTP server hostname"
  type        = string
  default     = "smtp.strato.de"
}

variable "smtp_port" {
  description = "SMTP server port"
  type        = string
  default     = "465"
}

variable "smtp_use_ssl" {
  description = "Use SSL for SMTP connection"
  type        = string
  default     = "true"
}

variable "smtp_username" {
  description = "SMTP username"
  type        = string
  sensitive   = true
}

variable "smtp_password" {
  description = "SMTP password"
  type        = string
  sensitive   = true
}

variable "from_email" {
  description = "From email address"
  type        = string
}

# Application configuration
variable "cors_origins" {
  description = "CORS allowed origins"
  type        = string
  default     = "*"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
} 