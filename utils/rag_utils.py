# utils/rag_utils.py
import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# ============================
# PATH CONFIGURATION
# ============================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
rag_folder = os.path.abspath(os.path.join(project_root, "knowledge"))  # or same as lightgbm_multi.pkl if needed

INDEX_PATH = os.path.join(rag_folder, "building_index.faiss")
TEXTS_PATH = os.path.join(rag_folder, "rag_texts.pkl")

# ============================
# MODEL LOADING
# ============================
model = SentenceTransformer("all-MiniLM-L6-v2")

# ============================
# FUNCTION DEFINITIONS
# ============================
def load_index_and_texts(index_path=INDEX_PATH, texts_path=TEXTS_PATH):
    index = faiss.read_index(index_path)
    with open(texts_path, "rb") as f:
        texts = pickle.load(f)
    return index, texts

def search_rag(query, k=5):
    index, texts = load_index_and_texts()
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k)
    results = [texts[i] for i in indices[0]]
    return results
