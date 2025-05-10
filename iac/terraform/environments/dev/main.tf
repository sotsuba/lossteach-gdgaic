module "gke-gdgaic-dev" {
    source      = "../../modules"
    project_id  = var.project_id
    region      = var.region
    
    cluster_name       = var.cluster_name
    cluster_version    = var.cluster_version
    cluster_node_count = var.cluster_node_count
    cluster_node_type  = var.cluster_node_type
    cluster_disk_type  = var.cluster_disk_type
    cluster_disk_size  = var.cluster_disk_size
}

