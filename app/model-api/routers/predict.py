import logging
import traceback
import numpy as np
import time
import onnxruntime as ort
import os
import tempfile

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, Query, UploadFile, HTTPException
from metrics import meter

from routers.schema.predict_response import PredictResponse
from routers.core.config import ModelConfig

#Utils
from utils.image_processing import (
    analyze_fragment_sizes,
    calculate_mask_metrics,
    calculate_size,
    conversion_func,
    preprocess_image,
)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ============= Model Loading =============
MODEL_CONFIG = ModelConfig()
try:
    ort.set_default_logger_severity(3)
    ort_session = ort.InferenceSession(
        MODEL_CONFIG.model_path,
        providers=['CPUExecutionProvider']  # Can be extended to include CUDA provider
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Model loaded successfully from {MODEL_CONFIG.model_path}")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    raise

# ============= Router Setup =============
router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = BASE_DIR / "app" / "model-api" / "tmp"

# ============= Metrics =============
counter = meter.create_counter(
    name="predict_counter",
    description="Number of predict images processed"
)

histogram = meter.create_histogram(
    name="predict_response_histogram",
    description="Predict response histogram",
    unit="seconds",
)
# ============= Main =============
@router.post("/predict")
async def predict(
    file: UploadFile = File(...), 
    score_threshold: float = Query(MODEL_CONFIG.scrore_threshold, ge=0.0, le=1.0),
    include_mask: bool = Query(False, description="Include binary mask data in response"),
    include_metrics: bool = Query(False, description="Include fragment metrics in response")
):
    # Mark the starting point for the response
    start_time = time.time()
    temp_path: Optional[str] = None
    logger.info("Sending POST /predict request!")
    try:
        logger.debug(f"Received prediction request for file: {file.filename}")

        # Read file content
        contents = await file.read()
        logger.debug(f"Read {len(contents)} bytes from file")

        # Save file temporarily
        temp_path = save_temp_file(contents)

        image_tensor = prepare_image(contents)

        # Run inference with timeout
        boxes, scores, mask_probs = run_inference(image_tensor, start_time)
        
        # Filter by score threshold
        mask = scores > score_threshold
        boxes = boxes[mask]
        scores = scores[mask]
        mask_probs = mask_probs[mask]

        if len(boxes) == 0:
            logger.warning("No fragments detected above threshold")
            return PredictResponse()

        # Calculate metrics for each mask only if requested
        boxes, scores, processed_masks, mask_metrics_list = process_masks(
            boxes, scores, mask_probs, start_time, include_metrics
        )

        # Ensure boxes is a numpy array
        if not isinstance(boxes, np.ndarray):
            boxes = np.array(boxes)

        # Create fragments list with all required fields
        return build_response(boxes, scores, processed_masks, mask_metrics_list, include_mask, include_metrics)

    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        ending_time = time.time()
        update_metrics({"api":"/predict"}, start_time, ending_time)
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_path}: {str(e)}")
    
def update_metrics(label: dict, starting_time, ending_time):
        # Increase the counter
        counter.add(1, label)
        # Mark the end of the response
        elapsed_time = ending_time - starting_time

        # Add histogram
        logger.info("elapsed time: ", elapsed_time)
        logger.info(elapsed_time)
        histogram.record(elapsed_time, label)
    

def prepare_image(contents: bytes) -> np.ndarray:
    # Preprocess image
    image_tensor = preprocess_image(contents)
    logger.debug(f"Preprocessed image shape: {image_tensor.shape}, dtype: {image_tensor.dtype}")

    # Validate input shape
    if not validate_input_shape(image_tensor):
        error_msg = f"Invalid input shape: {image_tensor.shape}. Expected shape: (-1, 3, 512, 512)"
        logger.error(error_msg)
        raise ValueError(error_msg)
    return image_tensor

def build_response(boxes, scores, processed_masks, mask_metrics_list, include_mask=False, include_metrics=False):
    size_metrics = analyze_fragment_sizes(boxes)
    fragments = []
    for i, (box, score, mask, metrics) in enumerate(zip(boxes, scores, processed_masks, mask_metrics_list)):
        # Calculate real size in cm
        size = calculate_size(box)
        real_size_cm = conversion_func(size)

        # Create fragment with optional fields
        fragment_data = {
            "id": int(i),
            "bbox": [int(x) for x in box.tolist()],
            "score": float(score),
            "size_cm": float(real_size_cm)
        }

        # Add optional fields if requested
        if include_mask:
            # Convert mask to a more efficient format for visualization
            x1, y1, x2, y2 = [int(coord) for coord in box]
            # Crop mask to bounding box
            cropped_mask = mask[y1:y2, x1:x2]
            # Convert to run-length encoding for efficient storage
            rle_mask = binary_mask_to_rle(cropped_mask)
            fragment_data["mask_data"] = {
                "rle": rle_mask,
                "bbox": [x1, y1, x2, y2],
                "shape": [y2-y1, x2-x1]  # Height, Width
            }
        if include_metrics:
            fragment_data["metrics"] = metrics

        fragments.append(fragment_data)

    return {
        "fragments": fragments,
        "size_metrics": size_metrics
    }

def binary_mask_to_rle(mask: np.ndarray) -> list:
    """Convert binary mask to run-length encoding format.
    Returns a list of [start, length] pairs where start is the index of the first 1
    and length is the number of consecutive 1s."""
    # Flatten the mask
    flat_mask = mask.flatten()
    rle = []
    start = None
    
    for i, val in enumerate(flat_mask):
        if val == 1 and start is None:
            start = i
        elif val == 0 and start is not None:
            rle.append([start, i - start])
            start = None
    
    # Handle case where mask ends with 1s
    if start is not None:
        rle.append([start, len(flat_mask) - start])
    
    return rle

def rle_to_binary_mask(rle, shape):
    """Convert run-length encoding back to binary mask.
    Args:
        rle: List of [start, length] pairs
        shape: [height, width] of the mask
    Returns:
        Binary mask of shape (height, width)
    """
    height, width = shape
    mask = np.zeros(height * width, dtype=np.uint8)
    
    for start, length in rle:
        if 0 <= start < len(mask) and length > 0:
            end = min(start + length, len(mask))
            mask[start:end] = 1
    
    return mask.reshape(height, width)

def run_inference(image_tensor: np.ndarray,  start_time: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ort_inputs = {ort_session.get_inputs()[0].name: image_tensor}
    if time.time() - start_time > MODEL_CONFIG.timeout:
            warning_msg = "Preprocessing took too long"
            logger.warning(warning_msg)
            raise TimeoutError(warning_msg)

    logger.info("Running inference...")
    ort_outs = ort_session.run(None, ort_inputs)
    
    # Debug: Log the shape and content details of model outputs
    for i, out in enumerate(ort_outs):
        logger.debug(f"Model output {i} shape: {out.shape}, dtype: {out.dtype}")
    
    # Important: The actual mask data is in ort_outs[3], not ort_outs[2]
    # ort_outs[2] contains scalar confidence values
    boxes, scores, mask_confidence = ort_outs[0], ort_outs[1], ort_outs[2]
    mask_probs = ort_outs[3]  # This contains the actual mask data
    
    logger.debug(f"Boxes shape: {boxes.shape}, dtype: {boxes.dtype}")
    logger.debug(f"Scores shape: {scores.shape}, dtype: {scores.dtype}")
    logger.debug(f"Mask confidence shape: {mask_confidence.shape}, dtype: {mask_confidence.dtype}")
    logger.debug(f"Mask probs shape: {mask_probs.shape}, dtype: {mask_probs.dtype}")
    
    # Check if we've exceeded the timeout
    if time.time() - start_time > MODEL_CONFIG.timeout:
        raise TimeoutError("Inference took too long")
    
    return boxes, scores, mask_probs

def process_masks(boxes, scores, mask_probs, start_time, include_metrics=False):
    mask_metrics_list = []
    processed_masks = []
    MASK_THRESHOLD = 0.5
    for i, (box, score, mask_prob) in enumerate(zip(boxes, scores, mask_probs)):
        # Check timeout
        if time.time() - start_time > MODEL_CONFIG.timeout:
            raise TimeoutError("Mask processing took too long")

        logger.debug(f"Processing mask {i}")

        if mask_prob.ndim == 3:  # If shape is [1, H, W]
            mask_prob = mask_prob.squeeze(0) if mask_prob.shape[0] == 1 else mask_prob[0]
        # Debug: Log mask probabilities
        logger.debug(f"Mask {i} shape: {mask_prob.shape}, min: {np.min(mask_prob)}, max: {np.max(mask_prob)}, mean: {np.mean(mask_prob)}")

        # Show histogram of mask probability values (debug)
        unique_values, counts = np.unique(mask_prob, return_counts=True)
        if len(unique_values) < 20:  # Only log if there aren't too many unique values
            logger.debug(f"Mask {i} unique probability values: {unique_values}")
            logger.debug(f"Mask {i} probability value counts: {counts}")
        else:
            logger.debug(f"Mask {i} has {len(unique_values)} unique values")

        # Convert box coordinates to integers and ensure they're within bounds
        x1, y1, x2, y2 = [int(coord) for coord in box]
        x1 = max(0, min(x1, 511))
        y1 = max(0, min(y1, 511))
        x2 = max(0, min(x2, 511))
        y2 = max(0, min(y2, 511))

        # Threshold the mask probabilities to get binary mask
        binary_mask = (mask_prob > MASK_THRESHOLD).astype(np.uint8)

        logger.debug(f"Binary mask {i} - min: {np.min(binary_mask)}, max: {np.max(binary_mask)}, mean: {np.mean(binary_mask)}")

        # Calculate metrics only if requested
        metrics = None
        if include_metrics:
            metrics = calculate_mask_metrics(binary_mask)
            logger.debug(f"Mask {i} metrics: {metrics}")
            mask_metrics_list.append(metrics)
        else:
            mask_metrics_list.append(None)

        processed_masks.append(binary_mask)
    return boxes, scores, processed_masks, mask_metrics_list

def save_temp_file(contents: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
    logger.debug(f"Saved file to {temp_path}")
    return temp_path 

def validate_input_shape(tensor: np.ndarray) -> bool:
    """Validate the input tensor shape."""
    expected_shape = (-1, 3, 512, 512)
    actual_shape = tensor.shape
    return all(exp in [-1, act] for exp, act in zip(expected_shape, actual_shape))

