import torch
import torchvision.io as io
import numpy as np
import cv2 # type: ignore
import logging
import tempfile
import os
import traceback
from routers.schema.predict_response  import SizeMetrics, SizeDistribution
from routers.schema.fragment          import FragmentMetrics

logger = logging.getLogger(__name__)

def preprocess_image(image_bytes):
    try:
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        try:
            return load_image(temp_path)
        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def load_image(temp_path):
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
        return FragmentMetrics()

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
        return FragmentMetrics()

    # Ensure the mask is 2D and binary (0 or 1)
    if len(mask_np.shape) > 2:
        logger.info(f"Squeezing mask from shape {mask_np.shape}")
        mask_np = mask_np.squeeze()  # Remove extra dimensions
        logger.info(f"After squeeze: {mask_np.shape}")

    # Ensure 2D array with correct dimensions (512x512)
    if mask_np.ndim == 1:
        logger.info(f"Converting 1D mask of length {mask_np.size} to 2D")
        if mask_np.size == 512 * 512:
            mask_np = mask_np.reshape(512, 512)
        else:
            # If it's not the right size, create a 512x512 array with the mask value
            mask_np = np.full((512, 512), mask_np[0] if mask_np.size > 0 else 0)

    # Convert to binary and ensure uint8
    if not np.issubdtype(mask_np.dtype, np.integer):
        logger.info(f"Converting mask from {mask_np.dtype} to binary uint8")
    
    # Count non-zero values before thresholding
    non_zero_count = np.count_nonzero(mask_np)
    logger.info(f"Non-zero values before thresholding: {non_zero_count} out of {mask_np.size} ({non_zero_count/mask_np.size*100:.2f}%)")
    
    # Apply threshold
    mask_np = (mask_np > 0.5).astype(np.uint8)

    # Debug logging after processing
    logger.info(f"Processed mask shape: {mask_np.shape}, dtype: {mask_np.dtype}, min: {np.min(mask_np)}, max: {np.max(mask_np)}")
    print("Mask min:", np.min(mask_np), "max:", np.max(mask_np), "shape:", mask_np.shape)
    
    # Count non-zero pixels in binary mask
    non_zero_binary = np.count_nonzero(mask_np)
    logger.info(f"Non-zero values after thresholding: {non_zero_binary} out of {mask_np.size} ({non_zero_binary/mask_np.size*100:.2f}%)")
    
    try:
        return find_contour(mask_np)
    except Exception as e:
        logger.error(f"Error in contour processing: {str(e)}")
        logger.error(f"Mask details - shape: {mask_np.shape}, dtype: {mask_np.dtype}, min: {np.min(mask_np)}, max: {np.max(mask_np)}")
        return FragmentMetrics()

def find_contour(mask_np):
    # Save the input mask to the contour function
    cv2.imwrite('contour_input_mask.png', mask_np * 255)
    
    # Handle the case of an empty mask
    if np.all(mask_np == 0):
        logger.warning("find_contour received an empty mask with no non-zero pixels")
        return FragmentMetrics()
    
    # Find contours
    try:
        contours, _ = cv2.findContours(mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print("Contours found:", len(contours))
        # Debug logging for contours
        logger.info(f"Found {len(contours)} contours")
        
        # Draw contours on a blank image for debugging
        if contours:
            contour_debug = np.zeros_like(mask_np)
            cv2.drawContours(contour_debug, contours, -1, 255, 1)
            cv2.imwrite('debug_contours.png', contour_debug)
            
            logger.info(f"First contour points: {len(contours[0])}")
    except Exception as e:
        logger.error(f"Error finding contours: {str(e)}")
        return FragmentMetrics()

    if not contours:
        logger.warning("No contours found in the binary mask")
        return FragmentMetrics()

    # Calculate metrics for the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest_contour)
    perimeter = cv2.arcLength(largest_contour, True)

    # Debug logging for metrics
    logger.info(f"Largest contour - Area: {area}, Perimeter: {perimeter}")
    
    # Draw the largest contour on a separate image
    largest_contour_debug = np.zeros_like(mask_np)
    cv2.drawContours(largest_contour_debug, [largest_contour], -1, 255, 1)
    cv2.imwrite('debug_largest_contour.png', largest_contour_debug)

    # Calculate circularity (4π * area / perimeter^2)
    circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0

    return FragmentMetrics(
        area=float(area),
        perimeter=float(perimeter),
        circularity=float(circularity),
        contour_count=len(contours)
    )

def analyze_fragment_sizes(boxes):
    """Analyze fragment sizes and return statistics."""
    # Convert boxes to CPU and numpy if it's a tensor
    if isinstance(boxes, torch.Tensor):
        boxes = boxes.detach().cpu().numpy()
    
    sizes = [calculate_size(box) for box in boxes]
    sizes = np.array(sizes)
    
    # Convert to real-world scale
    real_sizes = conversion_func(sizes)
    
    # Calculate histogram
    bins = np.linspace(0, np.max(real_sizes), 10)
    counts, _ = np.histogram(real_sizes, bins=bins)
    
    return SizeMetrics(
        min_size=float(np.min(real_sizes)),
        max_size=float(np.max(real_sizes)),
        mean_size=float(np.mean(real_sizes)),
        med_size=float(np.median(real_sizes)),
        std_size=float(np.std(real_sizes)),
        size_distribution=SizeDistribution(
            bins=bins.tolist(),
            counts=counts.tolist()
        )
    )