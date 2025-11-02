terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Static IP address for consistent access
resource "google_compute_address" "cvat_ip" {
  name   = "cvat-vm-ip"
  region = var.region
}

# Firewall rule to allow HTTP, HTTPS, and SSH
resource "google_compute_firewall" "cvat_firewall" {
  name    = "cvat-vm-firewall"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443", "8080"]
  }

  source_ranges = var.allowed_ips
  target_tags   = ["cvat-vm"]
}

# Persistent disk for CVAT data
resource "google_compute_disk" "cvat_data" {
  name = "cvat-data-disk"
  type = "pd-ssd"
  zone = var.zone
  size = var.data_disk_size_gb

  lifecycle {
    prevent_destroy = true
  }
}

# CVAT VM instance
resource "google_compute_instance" "cvat_vm" {
  name         = "cvat-annotation-vm"
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["cvat-vm"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50
      type  = "pd-standard"
    }
  }

  # Attach persistent data disk
  attached_disk {
    source      = google_compute_disk.cvat_data.id
    device_name = "cvat-data"
    mode        = "READ_WRITE"
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.cvat_ip.address
    }
  }

  metadata = {
    startup-script = file("${path.module}/../scripts/startup.sh")
    gcs-bucket     = var.gcs_bucket
  }

  service_account {
    email  = var.service_account_email
    scopes = ["cloud-platform"]
  }

  # Allow stopping for cost savings
  allow_stopping_for_update = true

  labels = {
    app     = "cvat"
    purpose = "annotation"
    project = "buffelgrass"
  }
}

# Output the VM's external IP
output "cvat_external_ip" {
  value       = google_compute_address.cvat_ip.address
  description = "External IP address for CVAT"
}

output "cvat_url" {
  value       = "http://${google_compute_address.cvat_ip.address}:8080"
  description = "CVAT web interface URL"
}

output "ssh_command" {
  value       = "gcloud --configuration=asdm compute ssh cvat-annotation-vm --zone=${var.zone}"
  description = "Command to SSH into the VM"
}

