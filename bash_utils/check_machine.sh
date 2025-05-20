#!/bin/bash
source ./logging_schema.sh

check_minikube() {
    MINIKUBE_STATUS=$(minikube status --format '{{.Host}}')
    if [ "$MINIKUBE_STATUS" != "Running" ]; then
        warning "Minikube is not running. Starting minikube..."
        minikube start
        if [ $? -ne 0 ]; then
            error_exit "Failed to start Minikube."
        fi
    else
        success "Minikube is running."
    fi
}

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error_exit "Docker daemon is not running. Please start Docker."
    else
        success "Docker daemon is running."
    fi
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        error_exit "$1 is not installed. Please install $1 first."
    else 
        success "$1 is existed on your machine!"
    fi
}

