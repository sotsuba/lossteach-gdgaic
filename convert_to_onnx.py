import torch
import torchvision
from torchvision.models.detection import maskrcnn_resnet50_fpn
import onnx
import onnxruntime
import os
import sys

class MaskRCNNWrapper(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, images):
        # The model returns a list of dicts (one per image)
        outputs = self.model(images)
        # For ONNX, return tensors (not list of dicts)
        # Here, just for the first image in the batch
        boxes = outputs[0]['boxes']
        scores = outputs[0]['scores']
        masks = outputs[0]['masks']  # [N, 1, H, W]
        return boxes, scores, masks

def convert_to_onnx(model_path, onnx_path):
    # Check if model file exists
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        print("Please provide the correct path to your .pth model file")
        sys.exit(1)

    try:
        # Load the PyTorch model
        print(f"Loading model from {model_path}")
        model = maskrcnn_resnet50_fpn(pretrained=False, num_classes=2)
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        model.eval()
        wrapper = MaskRCNNWrapper(model)

        # Create a dummy input with dynamic batch size
        dummy_input = torch.randn(1, 3, 512, 512)

        print("Exporting model to ONNX format...")
        # Export the model to ONNX
        torch.onnx.export(
            wrapper,
            dummy_input,
            onnx_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['boxes', 'scores', 'masks'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'boxes': {0: 'num_boxes'},
                'scores': {0: 'num_boxes'},
                'masks': {0: 'num_boxes'}
            }
        )

        # Verify the ONNX model
        print("Verifying ONNX model...")
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)

        # Test the ONNX model with ONNX Runtime
        print("Testing ONNX model with ONNX Runtime...")
        ort_session = onnxruntime.InferenceSession(onnx_path)
        ort_inputs = {ort_session.get_inputs()[0].name: dummy_input.numpy()}
        ort_outputs = ort_session.run(None, ort_inputs)
        
        print(f"\nModel successfully converted and verified!")
        print(f"Saved to: {onnx_path}")
        print(f"Input shape: {dummy_input.shape}")
        print(f"Number of outputs: {len(ort_outputs)}")
        
        # Print input and output details
        print("\nModel Input Details:")
        for input in ort_session.get_inputs():
            print(f"Name: {input.name}")
            print(f"Shape: {input.shape}")
            print(f"Type: {input.type}")
        
        print("\nModel Output Details:")
        for output in ort_session.get_outputs():
            print(f"Name: {output.name}")
            print(f"Shape: {output.shape}")
            print(f"Type: {output.type}")

    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Allow model path to be specified as command line argument
    model_path = sys.argv[1] if len(sys.argv) > 1 else "model.pth"
    onnx_path = sys.argv[2] if len(sys.argv) > 2 else "model.onnx"
    
    print(f"Converting model from {model_path} to {onnx_path}")
    convert_to_onnx(model_path, onnx_path) 