# ╔══════════════════════════════════════════════════════════╗
#   export_full_report.py  –  Cop:lot-style narrated report
# ╚══════════════════════════════════════════════════════════╝
#  Prereqs:  pip install fpdf2 matplotlib pandas
#  Font note: Georgia.ttf etc. must exist in C:\Windows\Fonts
# ─────────────────────────────────────────────────────────────

import os, re, json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF, XPos, YPos

# =====  directory & version filter  =========================
OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
VERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge", "iterations"))
os.makedirs(OUT_DIR, exist_ok=True)

SHOW_VERSIONS = []   # empty → include all

# =====  style helpers  ======================================
COLORS = ["#7EAECF", "#748DC2", "#B282C5", "#E88B86", "#F1B151", "#F2C92C"]
rgb = lambda hx: tuple(int(hx.lstrip("#")[i:i+2], 16) for i in (0,2,4))

def ascii_safe(t:str)->str:
    repl={"→":"->", "–":"-", "—":"-", "•":"-", "±":"+/-", "²":"2",
          "₁":"1","₂":"2","₃":"3"}
    for bad,good in repl.items(): t=t.replace(bad,good)
    return t

def beautify(k:str)->str:
    if "(" in k and ")" in k:
        a,b=k.split("(",1); a=re.sub(r"[_\-]"," ",a)
        a=re.sub(r"(?<=[a-z])(?=[A-Z])"," ",a)
        return f"{a.strip().title()} ({b.strip()}"
    k=re.sub(r"[_\-]"," ",k); k=re.sub(r"(?<=[a-z])(?=[A-Z])"," ",k)
    return k.strip().title()

def find_val(fragment: str, d: dict, default=0.0) -> float:
    for k, v in d.items():
        if fragment.lower() in k.lower():
            try: return float(v)
            except: return default
    return default

# =====  simple narration  ===================================
pct=lambda n,o:(n-o)/o*100 if o else 0
# ─── Narrative helpers  (place after pct=lambda n,o:...) ────

def describe_energy(df):
    lines = [describe(df["EUI"],     " kWh/m²a", "EUI"),
             describe(df["Cooling"], " kWh/m²a", "Cooling demand")]
    if df["Heating"].max() == 0:
        lines.append("No heating demand in any version.")
    else:
        lines.append(describe(df["Heating"], " kWh/m²a", "Heating demand"))
    return lines

def describe_carbon(df):
    return [describe(df["Operational"], " kg CO₂e/m²a", "Operational carbon"),
            describe(df["A-D"],         " kg CO₂e/m²a", "Embodied A-D")]

def describe_gwp(df):
    return [describe(df["Total"], " kg CO₂e/m²a", "Total GWP")]

def describe(series,unit="",label="Value"):
    if len(series)==1:
        return f"{label} is {series.iloc[0]:.0f}{unit}."
    first,last=series.iloc[0],series.iloc[-1]; d=pct(last,first)
    trend="rises" if d>0 else "falls" if d<0 else "remains unchanged"
    return (f"{label} {trend} from {first:.0f} to {last:.0f}{unit} "
            f"({d:+.0f} %).")

# =====  plot helpers  =======================================
def _axes(bottom=.25, show_xticks=False):
    ax=plt.gca()
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(left=False,bottom=False)
    if not show_xticks: ax.set_xticklabels([])
    plt.grid(axis="y",linestyle="--",alpha=.4)
    plt.subplots_adjust(bottom=bottom)

def bar(df,title,png):
    plt.figure(figsize=(7.5,4.5))
    bars=plt.bar(df["Metric"],df["Value"],
                 color=COLORS[:len(df)],edgecolor="#444",linewidth=.6)
    for b in bars:
        y=b.get_height(); plt.text(b.get_x()+b.get_width()/2,
        y+y*0.02,f"{y:.1f}",ha="center",va="bottom",fontsize=9)
    plt.legend(bars,df["Metric"],fontsize=8,ncol=len(df),
               loc="upper center",bbox_to_anchor=(0.5,-0.15),frameon=False)
    plt.title(title,fontsize=13,fontweight="bold"); _axes(); plt.tight_layout()
    plt.savefig(png,dpi=300,bbox_inches="tight"); plt.close()

def grouped(rows,png,title,ylabel,versions):
    n=len(rows); width=.8/n; plt.figure(figsize=(8,5))
    for idx,(lab,ser) in enumerate(rows):
        xs=[i+idx*width for i in range(len(versions))]
        plt.bar(xs,ser,width=width,color=COLORS[idx%len(COLORS)],
                edgecolor="#444",linewidth=.5,label=lab)
        for x,y in zip(xs,ser):
            plt.text(x,y+max(ser)*0.02,f"{y:.1f}",ha="center",va="bottom",fontsize=8)
    plt.xticks([i+width*(n-1)/2 for i in range(len(versions))],
               versions,fontsize=9)
    plt.title(title,fontsize=13,fontweight="bold");plt.ylabel(ylabel)
    _axes(.28,show_xticks=True)
    plt.legend(fontsize=8,ncol=n,loc="upper center",
               bbox_to_anchor=(0.5,-0.15),frameon=False)
    plt.tight_layout();plt.savefig(png,dpi=300,bbox_inches="tight");plt.close()

def gwp_trend(gdict,png):
    comps=["Embodied Carbon A-D (kg CO2e/m²a GFA)",
           "Operational Carbon (kg CO2e/m²a GFA)"]
    cols=[COLORS[3],COLORS[4]]
    vs=sorted(gdict)
    df=pd.DataFrame.from_dict(gdict,orient="index")[comps].reindex(vs)
    plt.figure(figsize=(8,5)); bottom=pd.Series(0,index=vs,dtype=float)
    for c,comp in zip(cols,comps):
        plt.bar(vs,df[comp],bottom=bottom,color=c,
                edgecolor="#444",linewidth=.5,label=beautify(comp))
        bottom+=df[comp]
    total=df.sum(axis=1)
    plt.plot(vs,total.values,marker="o",color=COLORS[1],linewidth=1.5,label="Total GWP")
    for i,v in enumerate(vs):
        plt.text(i,total.iloc[i]*1.02,f"{total.iloc[i]:.0f}",
                 ha="center",va="bottom",fontsize=9,fontweight="bold")
    plt.xticks(range(len(vs)),vs,fontsize=9)
    plt.title("GWP Trend per Design Iteration",fontsize=13,fontweight="bold")
    plt.ylabel("kg CO₂e/m²a GFA"); _axes(.28,show_xticks=True)
    plt.legend(fontsize=8,ncol=3,loc="upper center",
               bbox_to_anchor=(0.5,-0.15),frameon=False)
    plt.tight_layout();plt.savefig(png,dpi=300,bbox_inches="tight");plt.close()

# =====  PDF class  ==========================================
class PDF(FPDF):
    # --- small logo on every page except cover ---------------
    def header(self):
        if self.page_no()>1:
            try:self.image("logo.png",x=210-self.r_margin-18,y=5,w=18)
            except:pass
        if self.page_no()==1: return
        if hasattr(self,"head_title"):
            self.set_font("Georgia","B",12)
            self.set_text_color(*rgb(self.head_color))
            self.cell(0,10,ascii_safe(self.head_title),
                      align="C",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
    def footer(self):
        self.set_y(-15); self.set_font("Georgia","I",8)
        self.set_text_color(120); self.cell(0,10,f"Page {self.page_no()}",align="C")
    def hline(self):
        self.set_draw_color(200)
        self.line(self.l_margin,self.get_y(),210-self.r_margin,self.get_y())
    def wrap(self,text):
        maxw=self.w-self.l_margin-self.r_margin
        words=ascii_safe(text).split(); line=""
        for w in words:
            if self.get_string_width(line+w+" ")<maxw: line+=w+" "
            else:
                self.cell(0,6,line.strip(),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
                line=w+" "
        self.cell(0,6,line.strip(),new_x=XPos.LMARGIN,new_y=YPos.NEXT)

    # ---------- page builders --------------------------------
    def cover(self,ts):
        self.add_page()
        try:self.image("logo.png",x=(210-40)/2,y=15,w=40)
        except:pass
        self.ln(70)
        self.set_font("Georgia","B",24); self.set_text_color(*rgb(COLORS[0]))
        self.cell(0,10,"Building Performance Report",align="C",
                  new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.set_font("Georgia","I",12); self.ln(10)
        self.cell(0,10,f"Generated on {ts}",align="C",
                  new_x=XPos.LMARGIN,new_y=YPos.NEXT)

    def page_inputs(self,v,data):
        self.head_title=f"Input Parameters - {v}"; self.head_color=COLORS[2]
        self.add_page(); self.set_font("Georgia","B",14)
        self.set_text_color(*rgb(COLORS[2]))
        self.cell(0,10,"Input Parameters",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.hline(); self.ln(4)
        items=list(data.items()); self.set_font("Georgia","",10)
        self.set_text_color(33)
        for i in range(0,len(items),2):
            left=f"{beautify(items[i][0])}: {items[i][1]}"
            right=(f"{beautify(items[i+1][0])}: {items[i+1][1]}"
                   if i+1<len(items) else "")
            self.cell(95,8,left); self.cell(95,8,right,
                            new_x=XPos.LMARGIN,new_y=YPos.NEXT)

    def page_energy(self,v,outs,img):
        self.head_title=f"Energy Performance - {v}"; self.head_color=COLORS[0]
        self.add_page(); self.set_font("Georgia","B",14)
        self.set_text_color(*rgb(COLORS[0]))
        self.cell(0,10,"Energy Performance",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.hline(); self.ln(4)
        bullets=[
            f"EUI: {find_val('Energy Intensity',outs):.0f} kWh/m²a",
            f"Cooling: {find_val('Cooling Demand',outs):.0f} kWh/m²a",
            ("Heating: {find_val('Heating Demand',outs):.0f} kWh/m²a"
             if find_val('Heating Demand',outs)>0 else "No heating demand")
        ]
        self.set_font("Georgia","",10); self.set_text_color(33)
        for b in bullets: self.wrap(b)
        self.ln(2); self.image(img,x=15,w=180)

    def page_carbon(self,v,outs,img):
        self.head_title=f"Carbon Emissions - {v}"; self.head_color=COLORS[1]
        self.add_page(); self.set_font("Georgia","B",14)
        self.set_text_color(*rgb(COLORS[1]))
        self.cell(0,10,"Carbon Emissions",new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.hline(); self.ln(4)
        bullets=[
            f"Operational carbon: {find_val('Operational Carbon',outs):.0f} kg",
            f"Embodied A-D: {find_val('A-D',outs):.0f} kg",
            f"Total GWP: {find_val('GWP total',outs):.0f} kg"
        ]
        self.set_font("Georgia","",10); self.set_text_color(33)
        for b in bullets: self.wrap(b)
        self.ln(2); self.image(img,x=15,w=180)

    def text_page(self,title,cidx,paragraph,img):
        self.head_title=title; self.head_color=COLORS[cidx]
        self.add_page(); self.set_font("Georgia","B",14)
        self.set_text_color(*rgb(COLORS[cidx]))
        self.cell(0,10,title,new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.hline(); self.ln(4)
        self.set_font("Georgia","",10); self.set_text_color(33)
        self.wrap(paragraph); self.ln(3)
        self.image(img,x=15,w=180)

# =====  build PDF ===========================================
pdf = PDF()
# register Georgia (TTF paths may vary on non-English Windows)
pdf.add_font("Georgia", "",  r"C:\Windows\Fonts\georgia.ttf")
pdf.add_font("Georgia", "B", r"C:\Windows\Fonts\georgiab.ttf")
pdf.add_font("Georgia", "I", r"C:\Windows\Fonts\georgiai.ttf")
pdf.add_font("Georgia", "BI",r"C:\Windows\Fonts\georgiaz.ttf")


# load JSONs
vers = {}
version_pattern = re.compile(r"^V\d+\.json$", re.IGNORECASE)

for f in sorted(os.listdir(VERS_DIR)):
    if version_pattern.match(f):
        name = os.path.splitext(f)[0]
        with open(os.path.join(VERS_DIR, f)) as fp:
            vers[name] = json.load(fp)

if not vers: raise SystemExit("No JSON files found.")

# filter order for trend pages
order_all=sorted(vers)
order=[v for v in order_all if (not SHOW_VERSIONS) or (v in SHOW_VERSIONS)]
if not order: raise ValueError("None of SHOW_VERSIONS exist.")

# per-version charts + GWP data
gwp_data={}
for v,js in vers.items():
    outs=js["outputs"]
    en_png=os.path.join(OUT_DIR,f"energy_{v}.png")
    ca_png=os.path.join(OUT_DIR,f"carbon_{v}.png")
    bar(pd.DataFrame([
        ("Energy Intensity",find_val("Energy Intensity",outs)),
        ("Cooling Demand",  find_val("Cooling Demand",outs)),
        ("Heating Demand",  find_val("Heating Demand",outs))],
        columns=["Metric","Value"]),f"Energy KPIs – {v}",en_png)
    bar(pd.DataFrame([
        ("Operational", find_val("Operational Carbon", outs)),
        ("Embodied A-D",find_val("A-D", outs)),
        ("Total GWP",   find_val("GWP total", outs))],
        columns=["Metric","Value"]),f"Carbon KPIs – {v}",ca_png)
    gwp_data[v]={
        "Embodied Carbon A-D (kg CO2e/m²a GFA)": find_val("A-D",outs),
        "Operational Carbon (kg CO2e/m²a GFA)":  find_val("Operational Carbon",outs)
    }

# trend charts (only SHOW_VERSIONS)
en_trend_png=os.path.join(OUT_DIR,"energy_trend.png")
grouped([
    ("Energy Intensity",[find_val("Energy Intensity",vers[v]["outputs"]) for v in order]),
    ("Cooling Demand",  [find_val("Cooling Demand",  vers[v]["outputs"]) for v in order]),
    ("Heating Demand",  [find_val("Heating Demand",  vers[v]["outputs"]) for v in order])],
    en_trend_png,"Energy KPIs by Version","kWh/m²a",order)

ca_trend_png=os.path.join(OUT_DIR,"carbon_trend.png")
grouped([
    ("Operational", [find_val("Operational Carbon",vers[v]["outputs"]) for v in order]),
    ("Embodied A-D",[find_val("A-D",vers[v]["outputs"])                for v in order])],
    ca_trend_png,"Carbon Components by Version","kg CO₂e/m²a GFA",order)

gwp_trend_png=os.path.join(OUT_DIR,"gwp_trend.png")
gwp_trend({k:v for k,v in gwp_data.items() if k in order}, gwp_trend_png)

# DataFrames for narration
energy_df=pd.DataFrame({
    "EUI":[find_val("Energy Intensity",vers[v]["outputs"]) for v in order],
    "Cooling":[find_val("Cooling Demand",vers[v]["outputs"]) for v in order],
    "Heating":[find_val("Heating Demand",vers[v]["outputs"]) for v in order]}, index=order)

carbon_df=pd.DataFrame({
    "Operational":[find_val("Operational Carbon",vers[v]["outputs"]) for v in order],
    "A-D":[find_val("A-D",vers[v]["outputs"]) for v in order]}, index=order)

gwp_df=pd.DataFrame({
    "Total":[gwp_data[v]["Embodied Carbon A-D (kg CO2e/m²a GFA)"]+
             gwp_data[v]["Operational Carbon (kg CO2e/m²a GFA)"] for v in order]}, index=order)

# build report
pdf.cover(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
for v,js in vers.items():
    pdf.page_inputs(v,js["inputs_decoded"])
    pdf.page_energy(v,js["outputs"],os.path.join(OUT_DIR,f"energy_{v}.png"))
    pdf.page_carbon(v,js["outputs"],os.path.join(OUT_DIR,f"carbon_{v}.png"))

pdf.text_page("Energy Trend by Version",0," ".join(describe_energy(energy_df)),en_trend_png)
pdf.text_page("Carbon Trend by Version",1," ".join(describe_carbon(carbon_df)),ca_trend_png)
pdf.text_page("GWP Trend by Version",2," ".join(describe_gwp(gwp_df)),gwp_trend_png)

pdf_path=os.path.join(OUT_DIR,"Full_Building_Report.pdf")
pdf.output(pdf_path)
print("PDF and PNGs saved to:", OUT_DIR)
