import pandas as pd
import numpy as np
import time 
import requests
import logging 
from requests.exceptions import RequestException, ConnectionError
import src.config as config 
from   src.helpers import check_api_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_size_metrics_table(sizes):
    """Create a size metrics table for display"""
    data = {
        'Percentile': ['10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'],
        'Size (cm)': [np.percentile(sizes, p) for p in range(10, 101, 10)]
    }
    return pd.DataFrame(data)

def process_image(image_file, score_threshold=0.5):
    """Process the image through the API with retry logic"""
    try:
        return try_extract_image(image_file, score_threshold)
    except RequestException as e:
        logger.error(f"Error processing image: {str(e)}")
        raise ConnectionError(f"Failed to connect to Model API: {str(e)}") from e
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

def try_extract_image(image_file, score_threshold):
    # Check API health first
    if not check_api_health():
        raise ConnectionError("Model API is not available. Please try again later.")

    start_time = time.time()
    files = {"file": (image_file.name, image_file.getvalue())}
    params = {
        "score_threshold": score_threshold,
        "include_mask": True,  # Always request mask data
        "include_metrics": True  # Include metrics for visualization
    }

    response = requests.post(config.API_URL, files=files, params=params, timeout=30)
    process_time = time.time() - start_time

    if response.status_code != 200:
        error_msg = response.json().get('detail', 'Unknown error')
        if "numpy" in error_msg.lower() and "version" in error_msg.lower():
            raise ConnectionError(
                "Model API is experiencing compatibility issues with NumPy. "
                "Please contact support for assistance."
            )
        if "segmentation fault" in error_msg.lower():
            raise ConnectionError("Model API crashed. Please try again later.")

    return response, process_time
