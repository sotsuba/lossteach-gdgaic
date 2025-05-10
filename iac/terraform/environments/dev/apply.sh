#!/bin/bash

# Set variables
PROJECT_ID="gdgaic-lossteach"
CLUSTER_NAME="dev-cluster"
REGION="asia-east1"

# Function to check if cluster exists
check_cluster_exists() {
    gcloud container clusters describe $CLUSTER_NAME \
        --project $PROJECT_ID \
        --region $REGION >/dev/null 2>&1
    return $?
}

# Function to delete cluster
delete_cluster() {
    echo "Deleting existing cluster $CLUSTER_NAME..."
    gcloud container clusters delete $CLUSTER_NAME \
        --project $PROJECT_ID \
        --region $REGION \
        --quiet
}

# Main execution
echo "Checking if cluster $CLUSTER_NAME exists..."

if check_cluster_exists; then
    echo "Cluster exists. Proceeding with deletion..."
    delete_cluster
    echo "Waiting for cluster deletion to complete..."
else
    echo "Cluster does not exist. Proceeding with creation..."
fi

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Apply Terraform configuration
echo "Applying Terraform configuration..."
terraform apply -auto-approve

# Check if apply was successful
if [ $? -eq 0 ]; then
    echo "Terraform apply completed successfully!"
    gcloud config set project $PROJECT_ID
    gcloud config set compute/zone  "${REGION}-a"
    gcloud container clusters get-credentials $CLUSTER_NAME \
        --project $PROJECT_ID \
        --region $REGION
else
    echo "Terraform apply failed. Please check the error messages above."
    exit 1
fi 

