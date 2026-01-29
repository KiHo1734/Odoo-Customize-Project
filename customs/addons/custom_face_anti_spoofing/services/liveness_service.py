import os
import numpy as np

from .silence_anti_spoofing.src.anti_spoof_predict import AntiSpoofPredict
from .silence_anti_spoofing.src.generate_patches import CropImage
from .silence_anti_spoofing.src.utility import parse_model_name

# ===============================
# PATH FIX (สำคัญมาก)
# ===============================
SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
ANTI_SPOOF_BASE = os.path.join(SERVICE_DIR, "silence_anti_spoofing")
MODEL_DIR = os.path.join(ANTI_SPOOF_BASE, "resources", "anti_spoof_models")

if not os.path.exists(MODEL_DIR):
    raise FileNotFoundError(f"MODEL_DIR not found: {MODEL_DIR}")

_spoof_model = None
_cropper = CropImage()
_model_list = None

def get_engine():
    global _spoof_model, _model_list

    if _spoof_model is None:
        _spoof_model = AntiSpoofPredict(device_id=0)
        _model_list = [
            os.path.join(MODEL_DIR, f)
            for f in os.listdir(MODEL_DIR)
            if f.endswith(".pth")
        ]

    return _spoof_model, _model_list

def run_antispoof(image_bgr, bbox=None):
    spoof_model, model_list = get_engine()

    if bbox is None:
        h, w, _ = image_bgr.shape
        bbox = [0, 0, w, h]

    pred = np.zeros((1, 3))

    for model_path in model_list:
        model_name = os.path.basename(model_path) 

        h, w, _, s = parse_model_name(model_name)

        img = _cropper.crop(
            image_bgr,
            bbox,
            s,
            w,
            h,
            crop=True
        )

        pred += spoof_model.predict(img, model_path) 

    label = np.argmax(pred)
    return label == 1  
