import os
import torch
import clip
from PIL import Image
from torchvision import datasets
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px

# Setup
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Load dataset
dataset_path = "dataset"
dataset = datasets.ImageFolder(dataset_path, transform=preprocess)
class_names = dataset.classes

# Encode images
features = []
labels = []

loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=False)
with torch.no_grad():
    for images, targets in loader:
        images = images.to(device)
        image_features = model.encode_image(images)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        features.append(image_features.cpu().numpy())
        labels.extend(targets.numpy())

features = np.vstack(features)
labels = np.array(labels)

# Choose dimensionality reduction
use_tsne = True  # Set to False to use PCA instead

if use_tsne:
    reducer = TSNE(n_components=2, perplexity=5, init='pca', random_state=42)
else:
    reducer = PCA(n_components=2)

print("Reducing dimensions...")
features_2d = reducer.fit_transform(features)

df = pd.DataFrame({
    "x": features_2d[:, 0],
    "y": features_2d[:, 1],
    "label": [class_names[i] for i in labels]
})

# Plot
fig = px.scatter(
    df,
    x="x",
    y="y",
    color="label",
    title="CLIP Embeddings (t-SNE)",
    hover_name="label"
)
fig.show()