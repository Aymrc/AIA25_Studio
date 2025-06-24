import torch
import clip
from PIL import Image
import joblib
import numpy as np
import sys

# Load CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
model.eval()

# Load trained classifier + class names
checkpoint = joblib.load("clip_finetuned_w_linear_classifier.pkl")
clf = checkpoint["classifier"]
class_names = checkpoint["class_names"]

# Load and preprocess input image
image_path = sys.argv[1]  # e.g. >>>>>>>>> python D_predict_typology.py new_building.jpg <<<<<<<<<
image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)

# Encode image with CLIP
with torch.no_grad():
    image_feature = model.encode_image(image)
    image_feature /= image_feature.norm(dim=-1, keepdim=True)
    image_feature = image_feature.cpu().numpy()

# Predict
pred_class = clf.predict(image_feature)[0]
pred_label = class_names[pred_class]
print(f"Predicted typology: {pred_label}")
