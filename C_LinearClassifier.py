import os
import torch
import clip
from PIL import Image
from torchvision import datasets
from torchvision.transforms import Compose, Resize, CenterCrop, ToTensor, Normalize
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import numpy as np

# Setup
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Load dataset (folder structure should be class-labeled)
dataset_path = "dataset"
dataset = datasets.ImageFolder(dataset_path, transform=preprocess)
class_names = dataset.classes

# Split data
train_indices, test_indices = train_test_split(range(len(dataset)), test_size=0.2, stratify=dataset.targets, random_state=42)
train_subset = torch.utils.data.Subset(dataset, train_indices)
test_subset = torch.utils.data.Subset(dataset, test_indices)

# Encode all training images
def extract_features(subset):
    features = []
    labels = []
    loader = torch.utils.data.DataLoader(subset, batch_size=32, shuffle=False)
    with torch.no_grad():
        for images, targets in loader:
            images = images.to(device)
            image_features = model.encode_image(images)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            features.append(image_features.cpu().numpy())
            labels.extend(targets.numpy())
    return np.vstack(features), np.array(labels)

print("Encoding training set...")
X_train, y_train = extract_features(train_subset)

print("Encoding test set...")
X_test, y_test = extract_features(test_subset)

# Train linear classifier
print("Training classifier...")
clf = LogisticRegression(max_iter=1000, multi_class="multinomial", solver="lbfgs")
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=class_names))

# Save model (optional)
import joblib
joblib.dump({
    "classifier": clf,
    "class_names": class_names
}, "clip_finetuned_w_linear_classifier.pkl")