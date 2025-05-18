# Loss Teach GDGAIC: Blast Fragment Segmentation

## Teammates
* Nguyen Minh Duc (Leader)
* To Thanh Dat
* Nguyen Tien Son
## Mentor
* Ngo Hoang Bach

![Rock Fragment Detection](imgs/map.png)

# Local (without Docker)
### Step 1: Install necessary dependencies
```bash
pip install -r app/dashboard/requirements.txt
pip install -r app/model-api/requirements.txt
```

### Step 2: Run the backend
Terminal 1
```bash
make run_app
```

### Step 3: Run the frontend (on a new terminal)
Terminal 2
```bash
make run_dashboard
```
### Step 4: Access the frontend services: 
- The frontend will be hosted here: http://0.0.0.0:8501/

# Local (with Docker)
### Step 1: Make sure the Docker cluster is running

### Step 2: 
```bash
docker compose up --detach
```

### Step 3: Access the frontend services: 
- The frontend will be hosted here: http://0.0.0.0:8501/
# Cloud
still updating...
