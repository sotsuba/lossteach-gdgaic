# Rock Fragment Detection Dashboard

An advanced computer vision application that detects and analyzes rock fragments in images using machine learning.

![Rock Fragment Detection](docs/screenshot.png)

## Features

- **Fragment Detection**: Automatically identifies individual rock fragments in uploaded images
- **Size Measurement**: Calculates size metrics for each detected fragment
- **Statistical Analysis**: Provides size distribution analytics with visualizations
- **Interactive Visualizations**:
  - Combined mask visualization showing all fragments
  - Bounding box visualization with size labels
  - Individual fragment mask views
  - Size distribution charts
- **CI/CD Pipeline**: Automated testing and deployment using Jenkins
- **Infrastructure as Code**: Deployment configurations for Kubernetes and cloud environments
- **Reproducible Research**: Jupyter notebooks for model training and analysis

## System Architecture

The application consists of several key components:

1. **Model API** (Backend):
   - FastAPI-based REST API for rock fragment detection
   - ONNX runtime for efficient model inference
   - Image processing utilities for mask handling and metric calculation

2. **Dashboard** (Frontend):
   - Streamlit-based web interface for visualization and interaction
   - Interactive controls for image upload and fragment analysis
   - Statistical visualizations for fragment size distribution

3. **DevOps Infrastructure**:
   - Kubernetes deployment configuration for scalable hosting
   - Infrastructure as Code (IaC) for consistent environment setup
   - CI/CD pipeline for automated testing and deployment
   - Docker containers for consistent runtime environments

4. **Research & Development**:
   - Jupyter notebooks for model development and testing
   - Conversion scripts for model optimization (PyTorch → ONNX)
   - Metrics collection and visualization tools

## Local Development

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (recommended)
- pip and virtual environments

### Quick Start with Docker

The easiest way to run the application locally is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/sotsuba/lossteach-gdgaic.git
cd rock-fragment-detection

# Start the services
docker-compose up --build
```

This will start both the model API and dashboard services. Once running, you can access:

- Dashboard: http://localhost:8501
- Model API: http://localhost:8000

### Manual Setup (without Docker)

#### Backend (Model API)

```bash
cd app/model-api

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (Dashboard)

```bash
cd app/dashboard

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run main.py
```

### Running the Notebooks

To work with the Jupyter notebooks for model development:

```bash
# Navigate to notebooks directory
cd notebooks

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Start Jupyter
jupyter lab
```

## Cloud Deployment

### Kubernetes Deployment

The project includes Kubernetes manifests for scalable cloud deployment:

```bash
# Apply Kubernetes configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n rock-fragments

# Access the services
kubectl port-forward svc/dashboard -n rock-fragments 8501:8501
kubectl port-forward svc/model-api -n rock-fragments 8000:8000
```

### Infrastructure as Code

Infrastructure configuration is managed in the `iac/` directory:

1. **Cloud Resources**: Templates for provisioning cloud resources
2. **Network Configuration**: VPC, subnets, and security group definitions
3. **Database Setup**: Database instance and credentials management

To apply the infrastructure configurations:

```bash
# Navigate to the infrastructure directory
cd iac/

# Initialize the infrastructure provider
terraform init

# Plan the deployment
terraform plan -out=tfplan

# Apply the configuration
terraform apply tfplan
```

### CI/CD Pipeline with Jenkins

The repository includes Jenkins pipeline configurations for automated testing and deployment:

- `Jenkinsfile`: Main pipeline definition
- `docker-compose-jenkins.yml`: Jenkins service definition for local development

To set up the CI/CD pipeline:

1. Ensure Jenkins is configured with the required plugins:
   - Kubernetes
   - Docker
   - Pipeline
   - Git

2. Configure the Jenkins pipeline:
   ```bash
   # Start Jenkins locally for testing
   docker-compose -f docker-compose-jenkins.yml up
   ```

3. Create a new pipeline in Jenkins using the repository's Jenkinsfile

4. Configure the following environment variables in Jenkins:
   - `KUBE_CONFIG`: Base64-encoded Kubernetes configuration
   - `DOCKER_REGISTRY_CREDENTIALS`: Credentials for the Docker registry
   - `DEPLOYMENT_ENVIRONMENT`: Target environment (dev, staging, prod)

## Usage Guide

1. **Upload Images**:
   - Use the sidebar uploader to select rock fragment images (JPG, PNG supported)
   - Adjust the detection threshold if needed

2. **View Analysis**:
   - Select an image from the sidebar to see its analysis
   - Navigate through the tabs to see different visualizations
   - Fragment Detection: Shows combined masks and bounding boxes
   - Size Distribution: Displays statistical analysis of fragment sizes
   - Individual Fragments: Shows each detected fragment separately

3. **Interpret Results**:
   - Review fragment count and size metrics
   - Examine size distribution to understand fragment characteristics
   - View individual fragments for detailed inspection

## API Documentation

The Model API provides the following endpoints:

- `GET /health`: Health check endpoint
- `POST /predict`: Main prediction endpoint
  - Parameters:
    - `file`: The image file (multipart/form-data)
    - `score_threshold`: Detection confidence threshold (0.0-1.0)
    - `include_mask`: Whether to include binary mask data (boolean)
    - `include_metrics`: Whether to include metrics for each fragment (boolean)

For complete API documentation, visit http://localhost:8000/docs when the API is running.

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure all required packages are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Docker container fails to start**: Check Docker logs
   ```bash
   docker-compose logs
   ```

3. **Model API not responding**: Verify the model file exists and is accessible
   ```bash
   ls -la app/model-api/models/
   ```

4. **Kubernetes pods not starting**: Check pod status and logs
   ```bash
   kubectl describe pod <pod-name> -n rock-fragments
   kubectl logs <pod-name> -n rock-fragments
   ```

## Development

### Project Structure

```
app/
├── dashboard/          # Streamlit frontend
│   ├── main.py         # Main dashboard application
│   ├── src/            # Dashboard components
│   └── requirements.txt
├── model-api/          # FastAPI backend
│   ├── main.py         # API entrypoint
│   ├── routers/        # API endpoints
│   ├── utils/          # Utility functions
│   ├── models/         # ML model files
│   └── requirements.txt
k8s/                    # Kubernetes deployment manifests
iac/                    # Infrastructure as Code configurations
jenkins/                # Jenkins CI/CD configurations
notebooks/              # Jupyter notebooks for R&D
```

### Adding New Features

- **Backend**: Extend the API in `app/model-api/routers/`
- **Frontend**: Add new visualizations in `app/dashboard/src/visualization.py`
- **Deployment**: Update Kubernetes manifests in `k8s/` directory
- **Infrastructure**: Modify IaC configurations in `iac/` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The machine learning model uses a modified Mask R-CNN architecture
- Built with FastAPI, Streamlit, OpenCV, and PyTorch 