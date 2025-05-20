#!/bin/bash

# --- Source ---
source bash_utils/logging_schema.sh
source bash_utils/check_machine.sh
source bash_utils/utils.sh
LOG_FILE="/tmp/local_setup_with_k8s.log"

# --- Checking ---
check_command kubectl
check_command minikube
check_command docker
check_minikube 
check_docker 

# --- Main ---
kubectl apply -f k8s/local/namespace.yaml
kubectl apply -f k8s/local/deployment.yaml
log "Waiting for the deployment completed sucessfully... (10 seconds)"
loading 10
minikube service dashboard -n gdgaic 