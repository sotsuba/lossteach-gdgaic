#!/bin/bash

# --- Source ---
LOG_FILE="/tmp/local_setup_with_docker.log"
source bash_utils/logging_schema.sh
source bash_utils/check_machine.sh

# --- Checking ---
check_command docker
check_docker

# --- Main ---
success "Docker is installed. The docker images is building..."
docker compose -f docker-compose.app.yml up --remove-orphans --detach --build --quiet-pull > /dev/null 2>&1
success "The application is started successfully."
log "You can access this link: 0.0.0.0:8501"


