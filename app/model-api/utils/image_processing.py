import torch
import torchvision.io as io
import numpy as np
import cv2 # type: ignore
import logging
import tempfile
import os
import traceback

logger = logging.getLogger(__name__)

def preprocess_image(image_bytes):
    try:
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        try:
            return _extracted_from_preprocess_image_10(temp_path)
        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def _extracted_from_preprocess_image_10(temp_path):
    # Read image using torchvision.io
    image = io.read_image(temp_path)
    logger.info(f"Image loaded successfully. Shape: {image.shape}, dtype: {image.dtype}")

    # Add batch dimension and convert to float32
    image = image.unsqueeze(0)
    image = image.float()

    # Convert to numpy array
    image_np = image.numpy()

    logger.info(f"Image array shape after preprocessing: {image_np.shape}")
    return image_np

def calculate_size(boxes):
    x1, y1, x2, y2 = boxes
    return (y2 - y1) * (x2 - x1)

def conversion_func(size):
    '''Convert from area of bounding boxes to real-world scale'''
    conv_rate = 0.003  # 1pixel = 0.003cm = 3mm
    return conv_rate * size

def calculate_mask_metrics(mask):
    """Calculate mask metrics including area, perimeter, and circularity."""
    try:
        return try_calculate_mask_metrics(mask)
    except Exception as e:
        logger.error(f"Error in calculate_mask_metrics: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "area": 0,
            "perimeter": 0,
            "circularity": 0,
            "contour_count": 0
        }

def try_calculate_mask_metrics(mask):
    # Convert to numpy and ensure binary
    if isinstance(mask, torch.Tensor):
        mask_np = mask.detach().cpu().numpy()
    else:
        mask_np = np.array(mask)
    
    # Debug logging before processing
    logger.info(f"Initial mask shape: {mask_np.shape}, dtype: {mask_np.dtype}, min: {np.min(mask_np)}, max: {np.max(mask_np)}")
    
    # Handle scalar or empty arrays
    if mask_np.size == 0 or mask_np.ndim == 0:
        logger.warning("Empty or scalar mask received")
        return {
            "area": 0,
            "perimeter": 0,
            "circularity": 0,
            "contour_count": 0
        }
    
    # Ensure the mask is 2D and binary (0 or 1)
    if len(mask_np.shape) > 2:
        mask_np = mask_np.squeeze()  # Remove extra dimensions
    
    # Ensure 2D array with correct dimensions (512x512)
    if mask_np.ndim == 1:
        if mask_np.size == 512 * 512:
            mask_np = mask_np.reshape(512, 512)
        else:
            # If it's not the right size, create a 512x512 array with the mask value
            mask_np = np.full((512, 512), mask_np[0] if mask_np.size > 0 else 0)
    
    # Convert to binary and ensure uint8
    mask_np = (mask_np > 0.5).astype(np.uint8)

    # Debug logging after processing
    logger.info(f"Processed mask shape: {mask_np.shape}, dtype: {mask_np.dtype}, min: {np.min(mask_np)}, max: {np.max(mask_np)}")

    try:
        # Find contours
        contours, _ = cv2.findContours(mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Debug logging for contours
        logger.info(f"Found {len(contours)} contours")
        if contours:
            logger.info(f"First contour points: {len(contours[0])}")

        if not contours:
            return {
                "area": 0,
                "perimeter": 0,
                "circularity": 0,
                "contour_count": 0
            }

        # Calculate metrics for the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)

        # Debug logging for metrics
        logger.info(f"Largest contour - Area: {area}, Perimeter: {perimeter}")

        # Calculate circularity (4π * area / perimeter^2)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

        return {
            "area": float(area),
            "perimeter": float(perimeter),
            "circularity": float(circularity),
            "contour_count": len(contours)
        }
    except Exception as e:
        logger.error(f"Error in contour processing: {str(e)}")
        logger.error(f"Mask details - shape: {mask_np.shape}, dtype: {mask_np.dtype}, min: {np.min(mask_np)}, max: {np.max(mask_np)}")
        return {
            "area": 0,
            "perimeter": 0,
            "circularity": 0,
            "contour_count": 0
        }

def analyze_fragment_sizes(boxes):
    """Analyze fragment sizes and return statistics."""
    # Convert boxes to CPU and numpy if it's a tensor
    if isinstance(boxes, torch.Tensor):
        boxes = boxes.detach().cpu().numpy()
    
    sizes = [calculate_size(box) for box in boxes]
    sizes = np.array(sizes)
    
    # Convert to real-world scale
    real_sizes = conversion_func(sizes)
    
    return {
        "min_size": float(np.min(real_sizes)),
        "max_size": float(np.max(real_sizes)),
        "mean_size": float(np.mean(real_sizes)),
        "median_size": float(np.median(real_sizes)),
        "std_size": float(np.std(real_sizes)),
        "size_distribution": {
            "bins": np.linspace(0, np.max(real_sizes), 10).tolist(),
            "counts": np.histogram(real_sizes, bins=10)[0].tolist()
        }
    }