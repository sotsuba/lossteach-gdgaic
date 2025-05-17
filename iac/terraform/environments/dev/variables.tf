variable "project_id" {
    type        = string
    description = "The ID of the GCP project"
    default     = "gdgaic-lossteach"
}

variable "region" {
    type        = string
    description = "The region to deploy the resources to"
    default     = "asia-east1"
}

variable "zone" {
    type        = string
    description = "The zone to deploy the resources to"
    default     = "asia-east1-a"
}

variable "cluster_name" {
    type        = string
    description = "The name of the GKE cluster"
    default     = "dev-cluster"
}

variable "cluster_version" {
    type        = string
    description = "The version of the GKE cluster"
    default     = "1.24.10-gke.1000"
}

variable "cluster_node_count" {
    type        = number
    description = "The number of nodes in the GKE cluster"
    default     = 1
}

variable "cluster_node_type" {
    type        = string
    description = "The type of node to use in the GKE cluster"
    default     = "c2d-standard-4"
}

variable "cluster_disk_type" {
    type        = string
    description = "The type of disk to use in the GKE cluster"
    default     = "pd-standard"
}

variable "cluster_disk_size" {
    type        = number
    description = "The size of the disk to use in the GKE cluster"
    default     = 50
}

variable "cluster_enable_private_nodes" {
    type        = bool
    description = "Whether to enable private nodes in the GKE cluster"
    default     = true
}