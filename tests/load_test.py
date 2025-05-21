from locust import HttpUser, task, between # type: ignore #
import os
import logging

class ImageUploadUser(HttpUser):
    host = "http://localhost:5000"  # Specify the host URL
    wait_time = between(2, 3)
    
    def on_start(self):
        """Initialize test data"""
        self.test_image_path = os.path.join(os.path.dirname(__file__), "test_image.jpg")
        if not os.path.exists(self.test_image_path):
            logging.error(f"Test image not found at {self.test_image_path}")
            raise FileNotFoundError(f"Test image not found at {self.test_image_path}")

    @task
    def upload_image(self):
        try:
            with open(self.test_image_path, "rb") as image_file:
                # Add threshold parameter
                params = {
                    "threshold": "0.3"  # Match the API's default threshold
                }
                
                with self.client.post(
                    "/predict",
                    params=params,
                    files={"file": ("test_image.jpg", image_file, "image/jpeg")},
                    catch_response=True
                ) as response:
                    if response.status_code == 200:
                        response.success()
                    else:
                        response.failure(f"Failed with status {response.status_code}: {response.text}")
                    
        except Exception as e:
            logging.error(f"Error during upload: {str(e)}")
            raise
