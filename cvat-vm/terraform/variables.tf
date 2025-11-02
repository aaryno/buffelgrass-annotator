variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "asdm-399400"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-west1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-west1-b"
}

variable "machine_type" {
  description = "VM machine type"
  type        = string
  default     = "n2-standard-2" # 2 vCPU, 8 GB RAM
}

variable "data_disk_size_gb" {
  description = "Size of persistent data disk in GB"
  type        = number
  default     = 100
}

variable "gcs_bucket" {
  description = "GCS bucket for backups"
  type        = string
  default     = "gs://tumamoc-2023"
}

variable "allowed_ips" {
  description = "List of allowed IP ranges (use ['0.0.0.0/0'] for any IP)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict this to your IP range for better security
}

variable "service_account_email" {
  description = "Service account email for the VM (leave empty for default)"
  type        = string
  default     = ""
}

