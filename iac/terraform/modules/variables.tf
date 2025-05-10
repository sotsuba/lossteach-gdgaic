variable "project_id" {
    type = string
    description = "The ID of the GCP project"
}

variable "region" {
    type = string
    description = "The region to deploy the resources to"
}

variable "cluster_name" {
    type = string
    description = "The name of the GKE cluster"
}

variable "cluster_version" {
    type = string
    description = "The version of the GKE cluster"
}

variable "cluster_node_count" {
    type        = number
    description = "The number of nodes in the GKE cluster"
    default     = 1
}

variable "cluster_node_type" {
    type        = string
    description = "The type of node to use in the GKE cluster"
    default     = "e2-medium"
}

variable "cluster_disk_type" {
    type        = string
    description = "The type of disk to use in the GKE cluster"
    default     = "pd-ssd"
}

variable "cluster_disk_size" {
    type        = number
    description = "The size of the disk to use in the GKE cluster"
}
