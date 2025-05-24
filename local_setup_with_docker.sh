#!/bin/bash

# --- Source ---
LOG_FILE="/tmp/local_setup_with_docker.log"
source bash_utils/logging_schema.sh
source bash_utils/check_machine.sh

# --- Checking ---
check_command docker
check_docker

# --- Main ---
success "Docker is installed. The docker images is building... (about 1min)"
docker compose -f docker-compose.observable-app.yml up --remove-orphans --detach --build --quiet-pull 
success "The application is started successfully."
log "Service Dashboard: http://0.0.0.0:8501"
log "Model-api metrics: http://0.0.0.0:8099/metrics"
log "Container metrics: http://localhost:9100/metrics"
log "Prometheus     UI: http://0.0.0.0:9090"
log "Grafana        UI: http://0.0.0.0:3000"


