# Loss Teach GDGAIC: Blast Fragment Segmentation

# __Table of Contents__
[1. Introduction](#introduction)
- [1.1 About us](#about-us)
- [1.2 Overview](#overview)

[2. Technical Details](#technical-details)
- [2.1 Repository's structure](#repositorys-structure)
- [2.2 API Documentations](#api-documentation)

[3. Prerequisites](#prerequisites)

[4. Local Setup](#local-setup)

[5. Cloud Setup](#cloud-setup)

# Introduction
## About us
### Teammates
* Nguyen Minh Duc (Leader)
* To Thanh Dat
* Nguyen Tien Son
### Mentor
* Ngo Hoang Bach
## Overview

---
# __Technical Details__
## __Repository’s structure__
## __System Architecture__
![Rock Fragment Detection](imgs/map.png)
## __API Documentation__

---
# __Prerequisites__




# Local Setup
<h2 align="center"> <u>Easy Version</u> </h2>

* In this section, you only have to run some convenient bash scripts so that you can deploy the application easily.
* The scripts might not work properly on machine doesn't have Bash. You might have to run them on bash.

### __Local setup with Docker__
```bash
chmod +x local_setup_with_docker.sh
./local_setup_with_docker.sh
```


https://github.com/user-attachments/assets/a25b1eb2-cb33-4ae9-b712-138a6fe28fda



### __Local setup with Minikube__
```bash
chmod +x local_setup_with_minikube.sh
./local_setup_with_minikube.sh
```

https://github.com/user-attachments/assets/8b38a584-4790-485a-8c17-15dcac0da5be


<h2 align="center"> <u>Hard Version</u> </h2>

### __Local setup with Docker__ (Recommended)
#### Step 1: Start the Docker Engine or Docker Desktop if it doesn't start yet.
#### Step 2: Run the service
```bash
docker compose -f docker-compose.app.yml up --detach --build --remove-orphans
```
#### Step 3: Access the service
If things run properly, the service be hosted here: http://0.0.0.0:8501

https://github.com/user-attachments/assets/ad537d91-197a-48bf-99a4-9887fe4c00d7

### __Local setup with Minikube__
#### Step 0: Make sure the Docker Engine and Minikube is started
Run this on your terminal
```bash
minikube status 
```
If the console shows you this then you have to start the minikube first.
```bash
(gdgaic) sotsuba@SOTSUBA:~/gdgaic$ minikube status
minikube
type: Control Plane
host: Stopped
kubelet: Stopped
apiserver: Stopped
kubeconfig: Stopped
```
You can start the Minikube easily by using
```bash
minikube start
```

https://github.com/user-attachments/assets/28e12ee7-4430-49cb-9423-e00da4a48946

#### Step 1: Create a gdgaic namespace and switch to gdgaic namespace.
```bash
# Create the namespace from the YAML file
kubectl apply -f k8s/local/namespace.yaml

# Switch your current context to the 'gdgaic' namespace
kubens gdgaic
```

#### Step 2: Create the pods that support for the deployment and check if our pods are running
```bash
# Create the neccessary pods for deployment
kubectl apply -f k8s/local/deployment.yaml

# Check the pods status
kubectl get pods
```

Example of checking pods status.
```bash
(gdgaic) sotsuba@SOTSUBA:~/gdgaic$ k get pods
NAME                         READY   STATUS    RESTARTS   AGE
dashboard-5cbb49d686-xnvdb   1/1     Running   0          9s  # -> which means the dashboard is started successfully
model-api-844bc97bf7-szswg   0/1     Running   0          9s  # -> which means the model-api is not ready yet, you have to wait for that.
```

#### Step 4: Run the dashboard service
When you run the below command line, it will automatically export the Local IP out of the Kubernetes Cluster, so that you machine can access to the website.
```bash
minikube service dashboard -n gdgaic
```

#### Step 3: 

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

# Cloud Setup
still updating...
