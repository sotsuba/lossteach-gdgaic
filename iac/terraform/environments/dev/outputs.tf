output "cluster_info" {
    value = {
        name           = module.gke-gdgaic-dev.cluster_name
        location       = module.gke-gdgaic-dev.cluster_location
        endpoint       = module.gke-gdgaic-dev.cluster_endpoint
        host           = module.gke-gdgaic-dev.cluster_endpoint
    }
}