import os
import json
import torch
from PIL import Image
import cv2
from datetime import datetime
from diffusers import StableDiffusionXLPipeline

# ===============================
# CONFIGURATION
# ===============================
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
image_dir = os.path.join(project_root, "knowledge", "iterations")
render_dir = os.path.join(project_root, "knowledge", "renders")
os.makedirs(render_dir, exist_ok=True)

MODEL_FILE = "sdxlTurbo_sdxlTurboPruned.safetensors"
model_path = os.path.join("C:/ComfyUI_windows_portable/ComfyUI/models/checkpoints", MODEL_FILE)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ===============================
# LOAD PIPELINE FROM LOCAL MODEL
# ===============================
log("🚀 Initializing SDXL pipeline...")
try:
    pipe = StableDiffusionXLPipeline.from_single_file(
        model_path,
        torch_dtype=torch.float16,
        variant="fp16"
    ).to("cuda")
    pipe.set_progress_bar_config(disable=True)
    log("✅ Model loaded successfully.")
except Exception as e:
    log(f"❌ Failed to load model: {e}")
    exit(1)

# ===============================
# FUNCTIONS
# ===============================
def build_prompt(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        d = data.get("inputs_decoded", {})

        typology = d.get("Typology", "")
        roof = d.get("Roof_Partition", "")
        wall = d.get("Ext.Wall_Partition", "")
        glazing = d.get("Window-to-Wall_Ratio", "")

        prompt_parts = [
            "sustainable architecture",
            f"{typology.lower()} building" if typology else "",
            f"external walls made of {wall.lower()}" if wall else "",
            f"energy-efficient and biodiverse {roof.lower()} roof" if roof else "",
            f"{glazing.lower()} windows" if glazing else "",
            "eco-friendly design, ecological materials, passive solar design",
            "modern minimalism, clean lines, high detail render"
        ]
        return ", ".join(p for p in prompt_parts if p)
    except Exception as e:
        log(f"❌ Failed to build prompt from {json_path}: {e}")
        return "sustainable building, modern eco design"

def apply_canny(image_path):
    try:
        img = cv2.imread(image_path)
        img = cv2.resize(img, (1024, 1024))
        edges = cv2.Canny(img, 100, 200)
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(edges_rgb)
    except Exception as e:
        log(f"❌ Failed to apply Canny edge detection: {e}")
        return None

# ===============================
# MAIN BATCH LOOP
# ===============================
all_jsons = [f for f in os.listdir(image_dir) if f.startswith("V") and f.endswith(".json")]
log(f"🔍 Found {len(all_jsons)} version files to process.")

for json_file in all_jsons:
    base = os.path.splitext(json_file)[0]
    json_path = os.path.join(image_dir, json_file)
    image_path = os.path.join(image_dir, base + ".png")
    output_path = os.path.join(render_dir, base + "_render.png")

    if not os.path.exists(image_path):
        log(f"⚠️ Skipping {base} — PNG not found.")
        continue

    prompt = build_prompt(json_path)
    log(f"\n🎨 Rendering {base}")
    log(f"🧠 Prompt: {prompt}")

    control_image = apply_canny(image_path)
    if control_image is None:
        log(f"⚠️ Skipping {base} due to image processing error.")
        continue

    try:
        result = pipe(
            prompt=prompt,
            image=control_image,
            strength=0.6,
            guidance_scale=4.0,
            num_inference_steps=20
        ).images[0]
        result.save(output_path)
        log(f"✅ Render saved to: {output_path}")
    except Exception as e:
        log(f"❌ Generation failed for {base}: {e}")
