variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "wordbattle-1748668162"
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "europe-west3"  # Frankfurt region, similar to your eu-central-1 AWS region
}

variable "gcp_zone" {
  description = "GCP zone"
  type        = string
  default     = "europe-west3-a"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "wordbattle"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "wordbattle"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "postgres"
}

variable "db_instance_class" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"  # Smallest tier for cost efficiency, can be upgraded
}

variable "app_image_tag" {
  description = "Docker image tag for the application"
  type        = string
  default     = "latest"
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for production resources"
  type        = bool
  default     = true
}

variable "min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0  # 0 for cost efficiency, auto-scales up when needed
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 100
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run instances"
  type        = string
  default     = "2000m"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run instances"
  type        = string
  default     = "2Gi"
} 