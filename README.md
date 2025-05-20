# Loss Teach GDGAIC: Blast Fragment Segmentation

## Introduction

### Teammates
* Nguyen Minh Duc (Leader)
* To Thanh Dat
* Nguyen Tien Son
### Mentor
* Ngo Hoang Bach

---
![Rock Fragment Detection](imgs/map.png)
---

# Local Setup
## Easy version
* In this section, you only have to run some convenient bash scripts so that you can deploy the application easily.
* The scripts might not work properly on machine doesn't have Bash. You might have to run them on bash.

### __Local setup with Docker__
```bash
chmod +x local_setup_with_docker.sh
./local_setup_with_docker.sh
```

https://github.com/user-attachments/assets/3001ce59-7795-4b4a-ac64-ba1ce885d283

### __Local setup with Minikube__
```bash
chmod +x local_setup_with_minikube.sh
./local_setup_with_minikube.sh
```

https://github.com/user-attachments/assets/8b38a584-4790-485a-8c17-15dcac0da5be


## Hard Version
### __Local setup with Docker__ (Recommended)
#### Step 1: Start the Docker Engine or Docker Desktop if it doesn't start yet.
#### Step 2: Run the service
```bash
docker compose -f docker-compose.app.yml --detach --build --remove-orphans
```
#### Step 3: Access the service
If things run properly, the service be hosted here: http://0.0.0.0:8501

### __Local setup with Minikube__
#### Step 0: Make sure the minikube is started
Run this on your terminal
```bash
minikube status 
```
### __Local setup by yourself (no Docker, no Minikube) (not recommended)__

#### Step 0: create a virtual environment.
#### Step 1: Install necessary dependencies
```bash
pip install -r app/dashboard/requirements.txt
pip install -r app/model-api/requirements.txt
```
#### Step 2: Run the backend
Terminal 1
```bash
make run_app
```

#### Step 3: Run the frontend (on a new terminal)
Terminal 2
```bash
make run_dashboard
```
#### Step 4: Access the frontend service: 
- The frontend will be hosted here: http://0.0.0.0:8501/

## Local (with minikube)
### Option 1: Run the bash script for automation
```bash
chmod +x local_setup_with_minikube.sh
./local_setup_with_docker.sh
```
### Option 2: Manual run
#### Step 1: Install necessary dependencies
```bash
pip install -r app/dashboard/requirements.txt
pip install -r app/model-api/requirements.txt
```
#### Step 2: Run the backend
Terminal 1
```bash
make run_app
```

#### Step 3: Run the frontend (on a new terminal)
Terminal 2
```bash
make run_dashboard
```
#### Step 4: Access the frontend service: 
- The frontend will be hosted here: http://0.0.0.0:8501/

# Cloud
still updating...
