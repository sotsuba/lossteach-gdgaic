import logging
import traceback
import onnxruntime as ort
from pathlib import Path

logger = logging.getLogger(__name__)

# Get the model path
MODEL_PATH = Path(__file__).parent / "model.onnx"

def load_model(filepath=None, device=None):
    try:
        return try_load_model(MODEL_PATH)
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def try_load_model(filepath):
    # Create an ONNX Runtime session
    session = ort.InferenceSession(str(filepath))
    
    # Get the input name(s) for the model
    input_name = session.get_inputs()[0].name
    
    # Verify the model is loaded
    logger.info("ONNX model loaded successfully!")
    
    return session, input_name

# Load the model
model, input_name = load_model()