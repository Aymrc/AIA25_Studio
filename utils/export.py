# ╔══════════════════════════════════════════════════════════╗
#   export.py  –  Copilot-style narrated report with LLM
# ╚══════════════════════════════════════════════════════════╝

import os, re, json
from datetime import datetime
import pandas as pd
import plotly.express as px
from fpdf import FPDF, XPos, YPos
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server.config import client, completion_model

# =====  directory & version filter  =========================
OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
VERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge", "iterations"))
LOGO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui", "assets", "copilot_icon_chat.png"))
os.makedirs(OUT_DIR, exist_ok=True)

COLORS = ["#7EAECF", "#748DC2", "#B282C5", "#E88B86", "#F1B151", "#F2C92C"]
rgb = lambda hx: tuple(int(hx.lstrip("#")[i:i+2], 16) for i in (0,2,4))

BENCHMARKS = {
    "EUI": 175,
    "Operational": 130,
    "A-D": 6.5
}

def beautify(k: str) -> str:
    k = re.sub(r"[_\-]", " ", k)
    k = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", k)
    return k.strip().title()

def generate_input_narration(version_name, input_data):
    try:
        prompt = f"""
You are a sustainability design analyst reviewing architectural design inputs.
Below are the input parameters for version {version_name}. Write a 2–3 sentence commentary describing the design approach and sustainability context.
"""
        response = client.chat.completions.create(
            model=completion_model,
            messages=[{"role": "system", "content": prompt + json.dumps(input_data, indent=2)}],
            temperature=0.6,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "LLM error: input summary unavailable."

def generate_page_level_llm_description(page_title, data_dict):
    try:
        prompt = f"""
You are an expert in sustainable architecture. Write a brief, informative summary of the following data for the report section titled: {page_title}
"""
        response = client.chat.completions.create(
            model=completion_model,
            messages=[{"role": "system", "content": prompt + json.dumps(data_dict, indent=2)}],
            temperature=0.5,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "LLM error: section summary unavailable."

def get_val(frag, d):
    for k, v in d.items():
        if frag.lower() in k.lower():
            try: return round(float(v), 2)
            except: return 0.0
    return 0.0

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            try: self.image(LOGO_PATH, x=192, y=5, w=18)
            except: pass
        if hasattr(self, "head_title") and self.page_no() > 1:
            self.set_font("Georgia", "B", 12)
            self.set_text_color(*rgb(self.head_color))
            self.cell(0, 10, self.head_title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def hline(self):
        self.set_draw_color(200)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())

    def wrap(self, text):
        maxw = self.w - self.l_margin - self.r_margin
        words = text.split(); line = ""
        for w in words:
            if self.get_string_width(line + w + " ") < maxw:
                line += w + " "
            else:
                self.cell(0, 6, line.strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                line = w + " "
        self.cell(0, 6, line.strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def footer(self):
        self.set_y(-15)
        self.set_font("Georgia", "I", 8)
        self.set_text_color(120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def cover(self, ts):
        self.add_page()
        try: self.image(LOGO_PATH, x=(210 - 40)/2, y=15, w=40)
        except: pass
        self.ln(70)
        self.set_font("Georgia", "B", 24)
        self.set_text_color(*rgb(COLORS[0]))
        self.cell(0, 10, "Building Performance Report", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font("Georgia", "I", 12)
        self.ln(10)
        self.cell(0, 10, f"Generated on {ts}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def page_inputs(self, v, data):
        self.head_title = f"Input Parameters – {v}"
        self.head_color = COLORS[2]
        self.add_page()
        self.set_font("Georgia", "B", 14)
        self.set_text_color(*rgb(self.head_color))
        self.cell(0, 10, "Input Parameters", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.hline(); self.ln(4)

        items = list(data.items())
        self.set_font("Georgia", "", 10)
        self.set_text_color(33)
        for i in range(0, len(items), 2):
            left = f"{beautify(items[i][0])}: {items[i][1]}"
            right = f"{beautify(items[i+1][0])}: {items[i+1][1]}" if i + 1 < len(items) else ""
            self.cell(95, 8, left)
            self.cell(95, 8, right, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(5)
        self.wrap(generate_input_narration(v, data))

    def page_plot(self, title, data, img, color_index):
        self.head_title = title
        self.head_color = COLORS[color_index % len(COLORS)]
        self.add_page()
        self.set_font("Georgia", "B", 14)
        self.set_text_color(*rgb(self.head_color))
        self.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.hline(); self.ln(4)

        self.set_font("Georgia", "", 10)
        self.set_text_color(33)
        self.wrap(generate_page_level_llm_description(title, data))
        self.ln(4)

        if os.path.exists(img):
            self.image(img, x=15, w=180)

    def page_materials(self, v, image_path):
        self.head_title = f"Material System – {v}"
        self.head_color = COLORS[3]
        self.add_page()
        self.set_font("Georgia", "B", 14)
        self.set_text_color(*rgb(self.head_color))
        self.cell(0, 10, "Material System", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.hline(); self.ln(4)
        self.set_font("Georgia", "", 10)
        self.set_text_color(33)
        self.wrap(f"Commentary: The image below shows the mass model approach in version {v}, helping assess visually the design logic.")
        self.ln(4)
        if os.path.exists(image_path):
            self.image(image_path, x=15, w=180)

pdf = PDF()
pdf.add_font("Georgia", "",  r"C:\\Windows\\Fonts\\georgia.ttf")
pdf.add_font("Georgia", "B", r"C:\\Windows\\Fonts\\georgiab.ttf")
pdf.add_font("Georgia", "I", r"C:\\Windows\\Fonts\\georgiai.ttf")
pdf.add_font("Georgia", "BI",r"C:\\Windows\\Fonts\\georgiaz.ttf")

pdf.cover(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

vers = {}
for f in sorted(os.listdir(VERS_DIR)):
    if re.match(r"^V\d+\.json$", f, re.IGNORECASE):
        name = os.path.splitext(f)[0]
        with open(os.path.join(VERS_DIR, f)) as fp:
            vers[name] = json.load(fp)
order = sorted(vers)

def save_bar_plot(data_dict, title, path, benchmark=None):
    fig = px.bar(x=list(data_dict.keys()), y=list(data_dict.values()),
                 color=list(data_dict.keys()), text=[f"{v:.2f}" for v in data_dict.values()],
                 color_discrete_sequence=COLORS)
    if benchmark is not None:
        fig.add_hline(y=benchmark, line_dash="dash", line_color="red",
                      annotation_text="Benchmark", annotation_position="top right")
    fig.update_layout(
        title=title, plot_bgcolor='white', paper_bgcolor='white',
        width=640, height=400, margin=dict(l=20, r=20, t=40, b=20), font=dict(family="Georgia")
    )
    fig.write_image(path)

def save_trend(df, title, path):
    fig = px.line(df, markers=True, color_discrete_sequence=COLORS)
    fig.update_layout(
        title=title, plot_bgcolor='white', paper_bgcolor='white',
        width=700, height=400, margin=dict(l=20, r=20, t=40, b=20), font=dict(family="Georgia")
    )
    fig.write_image(path)

energy_records = []
carbon_records = []
gwp_records = []

for v, js in vers.items():
    pdf.page_inputs(v, js["inputs_decoded"])
    version_img_path = os.path.join(VERS_DIR, f"{v}.png")
    pdf.page_materials(v, version_img_path)

    energy_dict = {k: get_val(k, js["outputs"]) for k in ["Energy Intensity", "Cooling Demand", "Heating Demand"]}
    carbon_dict = {k: get_val(k, js["outputs"]) for k in ["Operational Carbon", "A-D", "GWP total"]}

    save_bar_plot(energy_dict, f"Energy – {v}", os.path.join(OUT_DIR, f"energy_{v}.png"), benchmark=BENCHMARKS["EUI"])
    save_bar_plot(carbon_dict, f"Carbon – {v}", os.path.join(OUT_DIR, f"carbon_{v}.png"), benchmark=BENCHMARKS["Operational"])

    pdf.page_plot(f"Energy Performance – {v}", js["outputs"], os.path.join(OUT_DIR, f"energy_{v}.png"), 0)
    pdf.page_plot(f"Carbon Emissions – {v}", js["outputs"], os.path.join(OUT_DIR, f"carbon_{v}.png"), 1)

    energy_records.append({"Version": v, **energy_dict})
    carbon_records.append({"Version": v, "Operational": carbon_dict["Operational Carbon"], "A-D": carbon_dict["A-D"]})
    gwp_records.append({"Version": v, "Total": carbon_dict["Operational Carbon"] + carbon_dict["A-D"]})

energy_df = pd.DataFrame(energy_records).set_index("Version")
carbon_df = pd.DataFrame(carbon_records).set_index("Version")
gwp_df = pd.DataFrame(gwp_records).set_index("Version")

save_trend(energy_df, "Energy Trend by Version", os.path.join(OUT_DIR, "energy_trend.png"))
save_trend(carbon_df, "Carbon Trend by Version", os.path.join(OUT_DIR, "carbon_trend.png"))
save_trend(gwp_df, "GWP Trend by Version", os.path.join(OUT_DIR, "gwp_trend.png"))

pdf.page_plot("Energy Trend by Version", energy_df.to_dict(), os.path.join(OUT_DIR, "energy_trend.png"), 0)
pdf.page_plot("Carbon Trend by Version", carbon_df.to_dict(), os.path.join(OUT_DIR, "carbon_trend.png"), 1)
pdf.page_plot("GWP Trend by Version", gwp_df.to_dict(), os.path.join(OUT_DIR, "gwp_trend.png"), 2)

pdf_path = os.path.join(OUT_DIR, "Full_Building_Report.pdf")
pdf.output(pdf_path)
print("✅ Report generated:", pdf_path)
