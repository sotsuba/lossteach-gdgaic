#!/bin/bash

# Check if minikube is installed
if ! command -v minikube &> /dev/null; then
  echo "Minikube is not installed. Please install Minikube first."
  exit 1
fi

# Check if minikube is running
MINIKUBE_STATUS=$(minikube status --format '{{.Host}}')
if [ "$MINIKUBE_STATUS" != "Running" ]; then
  echo "Minikube is not running. Starting minikube..."
  minikube start
  if [ $? -ne 0 ]; then
    echo "Failed to start Minikube."
    exit 1
  fi
else
  echo "Minikube is running."
fi

# Check if Docker daemon is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker daemon is not running. Please start Docker."
  exit 1
else
  echo "Docker daemon is running."
fi

echo "All checks passed. Minikube and Docker are ready."