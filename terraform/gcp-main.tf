terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

# Random password for Cloud SQL
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Random secret key
resource "random_password" "secret_key" {
  length  = 64
  special = false
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudsql.googleapis.com",
    "run.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "vpcaccess.googleapis.com",
    "compute.googleapis.com"
  ])
  
  service = each.value
  project = var.gcp_project_id
  
  disable_dependent_services = true
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.project_name}-${var.environment}-vpc"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "main" {
  name          = "${var.project_name}-${var.environment}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.gcp_region
  network       = google_compute_network.main.id
}

# VPC Access Connector for Cloud Run
resource "google_vpc_access_connector" "main" {
  name          = "${var.project_name}-${var.environment}-connector"
  region        = var.gcp_region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.main.name
  
  depends_on = [google_project_service.required_apis]
}

# Secrets in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "wordbattle-${var.environment}-db-password"
  
  replication {
    automatic = true
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "wordbattle-${var.environment}-secret-key"
  
  replication {
    automatic = true
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret      = google_secret_manager_secret.secret_key.id
  secret_data = random_password.secret_key.result
}

# Cloud SQL PostgreSQL instance
resource "google_sql_database_instance" "main" {
  name             = "${var.project_name}-${var.environment}-db"
  database_version = "POSTGRES_15"
  region           = var.gcp_region
  
  settings {
    tier = var.db_instance_class
    
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = google_compute_network.main.id
      enable_private_path_for_google_cloud_services = true
    }
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      location                       = var.gcp_region
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }
    
    database_flags {
      name  = "log_statement"
      value = "all"
    }
  }
  
  deletion_protection = var.environment == "prod" ? true : false
  
  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Private IP allocation for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-${var.environment}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Cloud SQL Database
resource "google_sql_database" "main" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

# Cloud SQL User
resource "google_sql_user" "main" {
  name     = var.db_username
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}

# Container Registry (Artifact Registry)
resource "google_artifact_registry_repository" "main" {
  location      = var.gcp_region
  repository_id = "${var.project_name}-${var.environment}"
  description   = "WordBattle Docker repository"
  format        = "DOCKER"
  
  depends_on = [google_project_service.required_apis]
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "${var.project_name}-${var.environment}-run"
  display_name = "WordBattle Cloud Run Service Account"
}

# IAM bindings for Cloud Run service account
resource "google_project_iam_member" "cloud_run_secrets" {
  project = var.gcp_project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "cloud_run_sql" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run Service
resource "google_cloud_run_service" "main" {
  name     = "${var.project_name}-${var.environment}"
  location = var.gcp_region
  
  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "100"
        "autoscaling.knative.dev/minScale"      = "1"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.main.connection_name
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.main.id
      }
    }
    
    spec {
      container_concurrency = 80
      timeout_seconds      = 300
      service_account_name = google_service_account.cloud_run.email
      
      containers {
        image = "${var.gcp_region}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.main.repository_id}/wordbattle-backend:latest"
        
        ports {
          container_port = 8000
        }
        
        env {
          name  = "DATABASE_URL"
          value = "postgresql://${google_sql_user.main.name}:${random_password.db_password.result}@${google_sql_database_instance.main.private_ip_address}:5432/${google_sql_database.main.name}"
        }
        
        env {
          name = "SECRET_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.secret_key.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
        
        env {
          name  = "PORT"
          value = "8000"
        }
        
        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
          requests = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [google_project_service.required_apis]
}

# Allow unauthenticated access to Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.main.name
  location = google_cloud_run_service.main.location
  role     = "roles/run.invoker"
  member   = "allUsers"
} 