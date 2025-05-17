import torch
from torchvision.models.detection import maskrcnn_resnet50_fpn_v2, MaskRCNN_ResNet50_FPN_V2_Weights
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor

def build_model(num_classes):
    weights = MaskRCNN_ResNet50_FPN_V2_Weights.COCO_V1
    model = maskrcnn_resnet50_fpn_v2(weights=weights)
    in_features_box = model.roi_heads.box_predictor.cls_score.in_features
    in_features_mask = model.roi_heads.mask_predictor.conv5_mask.in_channels
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features_box, num_classes)
    hidden_layer = 256
    model.roi_heads.mask_predictor = MaskRCNNPredictor(in_features_mask, hidden_layer, num_classes)
    return model

def convert_pth_to_onnx(pth_path, onnx_path, num_classes=2, input_shape=(1, 3, 512, 512), device='cpu'):
    model = build_model(num_classes)
    state_dict = torch.load(pth_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    model.to(device)

    dummy_input = torch.randn(*input_shape, device=device)
    # Export only the raw outputs (no postprocessing)
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        input_names=['input'],
        output_names=['boxes', 'labels', 'scores', 'masks'],
        opset_version=11,
        do_constant_folding=True,
        dynamic_axes={'input': {0: 'batch_size'}}
    )
    print(f"Exported to {onnx_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pth', type=str, required=True, help='Path to .pth file')
    parser.add_argument('--onnx', type=str, required=True, help='Output ONNX file')
    parser.add_argument('--num_classes', type=int, default=2, help='Number of classes (including background)')
    parser.add_argument('--input_size', type=int, nargs=2, default=[512, 512], help='Input H W')
    args = parser.parse_args()

    convert_pth_to_onnx(
        args.pth,
        args.onnx,
        num_classes=args.num_classes,
        input_shape=(1, 3, args.input_size[0], args.input_size[1])
    )