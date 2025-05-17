terraform {
    required_providers {
        google = {
            source = "hashicorp/google"
            version = "~> 4.0"
        }
    }
    required_version = ">= 1.0.0"
}

provider "google" {
    project = var.project_id
    region  = var.region
    zone    = "${var.region}-a"
}

resource "google_container_cluster" "primary" {
    project  = var.project_id
    name     = var.cluster_name
    location = var.region
    network  = "default"
    subnetwork = "default"

    # We can't create a cluster with no node pool defined, but we want to only use
    # separately managed node pools. So we create the smallest possible default
    # node pool and immediately delete it.
    remove_default_node_pool = true
    initial_node_count       = 1
    
    node_config {
        machine_type = var.cluster_node_type
        disk_type    = var.cluster_disk_type
        disk_size_gb = var.cluster_disk_size
        image_type   = "COS_CONTAINERD"
    }

    timeouts {
        create = "30m"
        update = "40m"
    }

    lifecycle {
        create_before_destroy = true
        ignore_changes = [name, location]
    }
}

resource "google_container_node_pool" "primary_nodes" {
    project  = var.project_id
    name     = "${var.cluster_name}-node-pool"
    location = var.zone
    cluster  = google_container_cluster.primary.name
        # node_count = var.cluster_node_count
    node_locations = ["asia-east1-a"]
    node_config {
        machine_type = var.cluster_node_type
        disk_type    = var.cluster_disk_type
        disk_size_gb = var.cluster_disk_size
        image_type   = "COS_CONTAINERD"
    }

    lifecycle {
        create_before_destroy = true
        ignore_changes = [name]
    }
}

data "google_client_config" "current" {}
