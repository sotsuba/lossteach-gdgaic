import os 

API_URL = os.getenv("MODEL_API_URL", "http://localhost:8000") + "/predict"
API_HEALTH_URL = os.getenv("MODEL_API_URL", "http://localhost:8000") + "/health"
MAX_FILES = 10
SUPPORTED_FORMATS = ["jpg", "jpeg", "png"]
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds