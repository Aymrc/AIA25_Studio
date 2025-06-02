# -*- coding: utf-8 -*-
import Rhino
import scriptcontext as sc
import System
import System.Net
import System.Text
import json
import threading
import time
import os

# === CONFIGURATION ===
def get_post_url():
    try:
        with open("knowledge/active_port.txt", "r") as f:
            port = f.read().strip()
        return "http://127.0.0.1:{}/rhino_data".format(port)
    except:
        return "http://127.0.0.1:5001/rhino_data"

POST_URL = get_post_url()
debounce_timer = None
is_running = False
last_event_time = 0
debounce_delay = 3  # seconds

# === POST METRICS ===
def post_json(url, data):
    try:
        client = System.Net.WebClient()
        client.Headers.Add("Content-Type", "application/json")
        body = System.Text.Encoding.UTF8.GetBytes(json.dumps(data))
        client.UploadData(url, "POST", body)
        Rhino.RhinoApp.WriteLine("Data successfully posted to server.")
        Rhino.RhinoApp.WriteLine("Posting to URL: " + url)
    except Exception as e:
        Rhino.RhinoApp.WriteLine("Error posting data: " + str(e))

# === SAVE METRICS LOCALLY ===
import os

def save_to_file(data):
    try:
        folder = "knowledge"  # Relative path
        if not os.path.exists(folder):
            os.makedirs(folder)

        path = os.path.join(folder, "geometry_metrics.json")
        with open(path, "w") as f:
            f.write(json.dumps(data, indent=2))

        Rhino.RhinoApp.WriteLine("Metrics saved to: " + path)
    except Exception as e:
        Rhino.RhinoApp.WriteLine("Error saving JSON: " + str(e))


# === MAIN METRICS COMPUTATION ===
def compute_total_metrics():
    total_volume = 0
    total_face_area = 0
    count = 0

    Rhino.RhinoApp.WriteLine("Computing total geometry metrics...")

    for obj in sc.doc.Objects:
        if not obj.IsSelectable() or not obj.Attributes.Visible:
            continue
        if not obj.IsValid:
            continue

        geom = obj.Geometry
        if isinstance(geom, Rhino.Geometry.Extrusion):
            geom = geom.ToBrep()

        if isinstance(geom, Rhino.Geometry.Brep) and geom.IsSolid:
            vol = Rhino.Geometry.VolumeMassProperties.Compute(geom)
            if vol:
                total_volume += vol.Volume
            for face in geom.Faces:
                area = Rhino.Geometry.AreaMassProperties.Compute(face)
                if area:
                    total_face_area += area.Area
            count += 1

        elif isinstance(geom, Rhino.Geometry.Mesh) and geom.IsClosed:
            vol = Rhino.Geometry.VolumeMassProperties.Compute(geom)
            if vol:
                total_volume += vol.Volume
            brep = Rhino.Geometry.Brep.CreateFromMesh(geom, False)
            if brep:
                for face in brep.Faces:
                    area = Rhino.Geometry.AreaMassProperties.Compute(face)
                    if area:
                        total_face_area += area.Area
            count += 1

    compactness = round(total_face_area / total_volume, 5) if total_volume > 0 else 0
    gfa = round(total_volume / 3, 3)

    payload = {
        "total_volume": round(total_volume, 3),
        "total_face_area": round(total_face_area, 3),
        "compactness": compactness,
        "gfa": gfa
    }

    Rhino.RhinoApp.WriteLine("Processed {} objects | Volume: {} | Area: {} | Compactness: {} | GFA: {}".format(
        count, payload["total_volume"], payload["total_face_area"], compactness, gfa
    ))

    post_json(POST_URL, payload)
    save_to_file(payload)

# === DEBOUNCING ===
def safe_compute():
    global is_running
    if is_running:
        Rhino.RhinoApp.WriteLine("Computation already in progress.")
        return
    is_running = True
    try:
        compute_total_metrics()
    finally:
        is_running = False

def debounce_refresh():
    global debounce_timer
    if debounce_timer and debounce_timer.is_alive():
        Rhino.RhinoApp.WriteLine("Debounce active, skipping trigger.")
        return

    def delayed_refresh():
        time.sleep(1.0)
        Rhino.RhinoApp.WriteLine("Debounced event triggered - computing metrics...")
        safe_compute()

    debounce_timer = threading.Thread(target=delayed_refresh)
    debounce_timer.start()

# === EVENT HANDLERS ===
def on_add(sender, e):
    Rhino.RhinoApp.WriteLine("Object added.")
    debounce_refresh()

def on_delete(sender, e):
    Rhino.RhinoApp.WriteLine("Object deleted.")
    debounce_refresh()

def on_replace(sender, e):
    Rhino.RhinoApp.WriteLine("Object replaced.")
    debounce_refresh()

def remove_listeners():
    try: Rhino.RhinoDoc.AddRhinoObject -= on_add
    except: pass
    try: Rhino.RhinoDoc.DeleteRhinoObject -= on_delete
    except: pass
    try: Rhino.RhinoDoc.ReplaceRhinoObject -= on_replace
    except: pass
    Rhino.RhinoApp.WriteLine("Removed existing event listeners.")

def setup_listeners():
    remove_listeners()
    Rhino.RhinoDoc.AddRhinoObject += on_add
    Rhino.RhinoDoc.DeleteRhinoObject += on_delete
    Rhino.RhinoDoc.ReplaceRhinoObject += on_replace
    Rhino.RhinoApp.WriteLine("Rhino listener is active and monitoring geometry changes.")

# === SCRIPT START ===
Rhino.RhinoApp.WriteLine("Starting Rhino listener script...")
setup_listeners()
compute_total_metrics()
Rhino.RhinoApp.WriteLine("Rhino listener initialized and ready.")
