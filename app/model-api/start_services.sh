#!/bin/bash

# Start Triton server in the background
tritonserver --model-repository=/app/model-api/models --http-port=8000 --grpc-port=8001 --metrics-port=8002 &

# Wait for Triton server to start
sleep 10

# Start FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8008 --reload 