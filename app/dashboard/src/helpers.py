import requests
from requests import RequestException
import logging 
from tenacity       import retry, stop_after_attempt, wait_exponential
import src.config as config 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(config.MAX_RETRIES),
    wait=wait_exponential(multiplier=config.INITIAL_RETRY_DELAY),
    reraise=True
)
def check_api_health():
    """Check if the model API is healthy with retry logic"""
    try:
        response = requests.get(config.API_HEALTH_URL, timeout=5)
        if response.status_code == 200:
            return True
        logger.error(f"API health check failed with status code: {response.status_code}")
        return False
    except RequestException as e:
        logger.error(f"API health check failed: {str(e)}")
        raise
