# Infrastructure as Code and CI/CD Setup

This repository contains the infrastructure as code (IaC) and CI/CD configurations for managing Kubernetes clusters and Jenkins pipelines.

## Directory Structure

### Terraform
- `terraform/modules/`: Contains reusable Terraform modules for infrastructure components
  - `main.tf`: Main module configuration
  - `variables.tf`: Module input variables
  - `outputs.tf`: Module outputs

- `terraform/environments/`: Environment-specific configurations
  - `dev/`: Development environment
  - `staging/`: Staging environment
  - `prod/`: Production environment

### Jenkins
- `jenkins/jobs/`: Jenkins job definitions
- `jenkins/pipelines/`: Jenkins pipeline definitions
  - `k8s-deploy.groovy`: Kubernetes deployment pipeline
- `jenkins/config/`: Jenkins configuration files
  - `credentials.xml`: Jenkins credentials configuration

## Setup Instructions

### Prerequisites
- Terraform >= 1.0.0
- Jenkins >= 2.387.1
- Kubernetes cluster access
- GitHub repository access

### Getting Started
1. Configure your environment variables and credentials
2. Initialize Terraform in the desired environment directory
3. Apply Terraform configurations
4. Configure Jenkins with the provided pipeline definitions

## Security Notes
- Never commit sensitive credentials to version control
- Use environment variables or secure credential storage
- Follow the principle of least privilege for all service accounts 