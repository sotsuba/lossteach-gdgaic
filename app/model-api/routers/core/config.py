from pydantic import BaseModel
import os

class ModelConfig(BaseModel):
    model_path:         str   = os.path.join(os.path.dirname(__file__),'..','..', 'models','model.onnx')
    scrore_threshold:   float = 0.3
    input_size:         tuple = (512, 512)
    device:             str   = "cpu"
    timeout:            int   = 30