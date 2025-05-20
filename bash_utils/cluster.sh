#!/bin/bash

# Set variables
PROJECT_ID="gdgaic-lossteach"
CLUSTER_NAME="dev-cluster"
REGION="asia-east1"
ZONE="asia-east1-a"
LOG_FILE="/tmp/cluster.log"
source ./logging_schema.sh

# --- Function ---

check_cluster_exists() {
    gcloud container clusters describe $CLUSTER_NAME \
        --project $PROJECT_ID \
        --region $REGION >/dev/null 2>&1
    return $?
}

delete_cluster() {
    warning "Deleting existing cluster $CLUSTER_NAME..."
    gcloud container clusters delete $CLUSTER_NAME \
        --project $PROJECT_ID \
        --region $REGION \
        --quiet
}


# ------ Main ------
log "Checking if cluster $CLUSTER_NAME exists..."

if check_cluster_exists; then
    log "Cluster exists. Proceeding with deletion..."
    delete_cluster
    log "Waiting for cluster deletion to complete..."
else
    warning "Cluster does not exist. Proceeding with creation..."
fi

# Initialize Terraform
cd iac/terraform/environments/dev
log "Initializing Terraform..."
terraform init

# Apply Terraform configuration
log "Applying Terraform configuration..."
terraform apply -auto-approve

# Check if apply was successful
if [ $? -eq 0 ]; then
    success "Terraform apply completed successfully!"
    log "Trying to attach the cluster to terminal..."
    gcloud config set project $PROJECT_ID
    gcloud config set compute/zone  $ZONE
    gcloud container clusters get-credentials $CLUSTER_NAME \
        --project $PROJECT_ID \
        --region $REGION
    success "The GKE clusters was attached to this terminal"
else
    error_exit "Terraform apply failed. Please check the error messages above."
fi 

