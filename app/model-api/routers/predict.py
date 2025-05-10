import logging
import traceback
import numpy as np
import onnxruntime as ort
import time
import os
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, Query, UploadFile, HTTPException
from utils.image_processing import (
    analyze_fragment_sizes,
    calculate_mask_metrics,
    calculate_size,
    conversion_func,
    preprocess_image,
)

# Import torch after other imports to avoid circular dependencies
import torch  # type: ignore

# ============= Configuration =============
# Model configuration
MODEL_CONFIG = {
    "model_path": os.path.join(os.path.dirname(__file__), '..', 'models', 'model.onnx'),
    "score_threshold": 0.3,
    "input_size": (512, 512),  # (height, width)
    "device": "cpu",  # or "cuda" for GPU
    "timeout": 30,  # Maximum time in seconds for inference
}

# ============= Model Loading =============
try:
    ort_session = ort.InferenceSession(
        MODEL_CONFIG["model_path"],
        providers=['CPUExecutionProvider']  # Can be extended to include CUDA provider
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Model loaded successfully from {MODEL_CONFIG['model_path']}")
except Exception as e:
    logger.error(f"Failed to load model: {str(e)}")
    raise

# ============= Router Setup =============
router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = BASE_DIR / "app" / "model-api" / "tmp"

def validate_input_shape(tensor: np.ndarray) -> bool:
    """Validate the input tensor shape."""
    expected_shape = (-1, 3, 512, 512)
    actual_shape = tensor.shape
    return all(exp in [-1, act] for exp, act in zip(expected_shape, actual_shape))

@router.post("/predict")
async def predict(
    file: UploadFile = File(...), 
    score_threshold: float = Query(MODEL_CONFIG["score_threshold"], ge=0.0, le=1.0)
):
    start_time = time.time()
    temp_path: Optional[str] = None
    
    try:
        logger.info(f"Received prediction request for file: {file.filename}")

        # Read file content
        contents = await file.read()
        logger.info(f"Read {len(contents)} bytes from file")

        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
            logger.info(f"Saved file to {temp_path}")
        
        # Preprocess image
        image_tensor = preprocess_image(contents)
        logger.info(f"Preprocessed image shape: {image_tensor.shape}, dtype: {image_tensor.dtype}")

        # Validate input shape
        if not validate_input_shape(image_tensor):
            raise ValueError(f"Invalid input shape: {image_tensor.shape}. Expected shape: (-1, 3, 512, 512)")

        # Run inference with timeout
        ort_inputs = {ort_session.get_inputs()[0].name: image_tensor}
        
        # Check if we've exceeded the timeout
        if time.time() - start_time > MODEL_CONFIG["timeout"]:
            raise TimeoutError("Preprocessing took too long")
            
        logger.info("Running inference...")
        ort_outs = ort_session.run(None, ort_inputs)
        
        # Check if we've exceeded the timeout
        if time.time() - start_time > MODEL_CONFIG["timeout"]:
            raise TimeoutError("Inference took too long")
        
        # Process outputs
        boxes = ort_outs[0]  # Shape: [N, 4]
        scores = ort_outs[1]  # Shape: [N]
        mask_probs = ort_outs[2]  # Shape: [N, H, W] or [N, 1, H, W]
            
        # Debug logging for outputs
        logger.info(f"Boxes shape: {boxes.shape}, dtype: {boxes.dtype}")
        logger.info(f"Scores shape: {scores.shape}, dtype: {scores.dtype}")
        logger.info(f"Mask probabilities shape: {mask_probs.shape}, dtype: {mask_probs.dtype}")
            
        # Filter by score threshold
        mask = scores > score_threshold
        boxes = boxes[mask]
        scores = scores[mask]
        mask_probs = mask_probs[mask]
        
        if len(boxes) == 0:
            logger.warning("No fragments detected above threshold")
            return {
                "fragments": [],
                "size_metrics": {
                    "min_size": 0.0,
                    "max_size": 0.0,
                    "mean_size": 0.0,
                    "median_size": 0.0,
                    "std_size": 0.0,
                    "size_distribution": {
                        "bins": [],
                        "counts": []
                    }
                }
            }
            
        # Calculate metrics for each mask
        mask_metrics_list = []
        processed_masks = []
        
        MASK_THRESHOLD = 0.5
        for i, (box, score, mask_prob) in enumerate(zip(boxes, scores, mask_probs)):
            # Check timeout
            if time.time() - start_time > MODEL_CONFIG["timeout"]:
                raise TimeoutError("Mask processing took too long")
                
            logger.info(f"Processing mask {i}")
                
            # Convert box coordinates to integers and ensure they're within bounds
            x1, y1, x2, y2 = [int(coord) for coord in box]
            x1 = max(0, min(x1, 511))
            y1 = max(0, min(y1, 511))
            x2 = max(0, min(x2, 511))
            y2 = max(0, min(y2, 511))
                
            # Process mask probabilities
            if mask_prob.ndim == 3:  # If shape is [1, H, W]
                mask_prob = mask_prob.squeeze(0)  # Convert to [H, W]
            elif mask_prob.ndim == 0:  # If scalar
                mask_prob = np.full((512, 512), mask_prob)

            # Threshold the mask probabilities to get binary mask
            binary_mask = (mask_prob > MASK_THRESHOLD).astype(np.uint8)

            # Debug logging for individual mask
            logger.info(f"Mask {i} shape: {binary_mask.shape}, dtype: {binary_mask.dtype}, min: {np.min(binary_mask)}, max: {np.max(binary_mask)}")
            logger.info(f"Box coordinates: x1={x1}, y1={y1}, x2={x2}, y2={y2}")
            logger.info(f"Mask probability: {score}")
                
            # Convert to torch tensor for processing
            mask_tensor = torch.from_numpy(binary_mask.copy())  # Make a copy to ensure contiguous array
                
            # Calculate metrics
            metrics = calculate_mask_metrics(mask_tensor)
            mask_metrics_list.append(metrics)
            processed_masks.append(binary_mask.tolist())

        # Ensure boxes is a numpy array
        if not isinstance(boxes, np.ndarray):
            boxes = np.array(boxes)
            
        # Calculate size metrics
        size_metrics = analyze_fragment_sizes(boxes)
            
        # Create fragments list with all required fields
        fragments = []
        for i, (box, score, mask, metrics) in enumerate(zip(boxes, scores, processed_masks, mask_metrics_list)):
            # Calculate real size in cm
            size = calculate_size(box)
            real_size_cm = conversion_func(size)
            
            # Create a more compact fragment representation
            fragment = {
                "id": i,
                "bbox": [int(x) for x in box.tolist()],
                "score": float(score),
                "size_cm": float(real_size_cm),
                "mask_data": mask,  # The actual binary mask data
                "metrics": {
                    "area": float(metrics["area"]),
                    "perimeter": float(metrics["perimeter"]),
                    "circularity": float(metrics["circularity"])
                }
            }
            fragments.append(fragment)

        return {
            "fragments": fragments,
            "size_metrics": size_metrics
        }

    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_path}: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if model is loaded
        if ort_session is None:
            raise RuntimeError("Model not loaded")
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
