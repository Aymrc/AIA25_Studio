# -*- coding: utf-8 -*-
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
import System.Drawing
import Rhino.Display

import System
import System.Net
import System.Text
import json
import threading
import time
import os
import collections
from collections import OrderedDict

# === CONFIGURATION ===
POST_URL = "http://127.0.0.1:5005/geometry"
debounce_timer = None
is_running = False
listener_active = True

def capture_viewport(version_name, output_folder):
    import Rhino
    import scriptcontext as sc
    import System
    import System.Drawing
    import os

    version_name = version_name.strip().split()[0]
    Rhino.RhinoApp.WriteLine("[📸] Starting USER VIEW capture for: {}".format(version_name))

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        Rhino.RhinoApp.WriteLine("[📁] Created folder: {}".format(output_folder))

    filepath = os.path.join(output_folder, "{}_user.png".format(version_name))
    Rhino.RhinoApp.WriteLine("[💾] Saving to: {}".format(filepath))

    try:
        view = sc.doc.Views.Find("Perspective", False)
        if not view:
            Rhino.RhinoApp.WriteLine("[⚠️] 'Perspective' view not found. Using ActiveView instead.")
            view = sc.doc.Views.ActiveView

        if not isinstance(view, Rhino.Display.RhinoView):
            Rhino.RhinoApp.WriteLine("[❌] Invalid view type: {}".format(type(view)))
            return

        view.Redraw()
        size = view.ActiveViewport.Size
        width, height = size.Width, size.Height
        Rhino.RhinoApp.WriteLine("[ℹ️] Viewport size: {} x {}".format(width, height))

        # Use only attributes known to work in IronPython + Rhino 8
        settings = Rhino.Display.ViewCaptureSettings(view, System.Drawing.Size(width, height), 96)

        bitmap = Rhino.Display.ViewCapture.CaptureToBitmap(settings)
        if bitmap:
            bitmap.Save(filepath)
            Rhino.RhinoApp.WriteLine("[✅] Image saved: {}".format(filepath))
        else:
            Rhino.RhinoApp.WriteLine("[❌] Bitmap capture returned None.")

    except Exception as e:
        Rhino.RhinoApp.WriteLine("[🚨] Exception during capture: {}".format(e))



# === POST METRICS ===
def post_json(url, data):
    try:
        client = System.Net.WebClient()
        client.Headers.Add("Content-Type", "application/json")
        body = System.Text.Encoding.UTF8.GetBytes(json.dumps(data))
        client.UploadData(url, "POST", body)
        Rhino.RhinoApp.WriteLine("\u2705 Data successfully posted to server.")
        Rhino.RhinoApp.WriteLine("\ud83d\udce1 Posting to URL: " + url)
    except Exception as e:
        Rhino.RhinoApp.WriteLine("\u274c Error posting data: " + str(e))

# === SAVE METRICS LOCALLY ===
def save_to_file(data):
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        folder = os.path.join(project_root, "knowledge")
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = os.path.join(folder, "geometry_metrics.json")
        Rhino.RhinoApp.WriteLine("\ud83d\udcdd Saving data:\n" + json.dumps(data, indent=2))
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        Rhino.RhinoApp.WriteLine("\ud83d\udcce Metrics saved to: " + path)
    except Exception as e:
        Rhino.RhinoApp.WriteLine("\u274c Error saving JSON: " + str(e))

# === MAIN METRICS COMPUTATION ===
def update_compiled_ml_data(gfa_value, av_value):
    path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "compiled_ml_data.json")
    with open(path, "r") as f:
        data = json.load(f)

    ordered_data = OrderedDict()
    ordered_data["ew_par"] = data.get("ew_par", 0)
    ordered_data["ew_ins"] = data.get("ew_ins", 0)
    ordered_data["iw_par"] = data.get("iw_par", 0)
    ordered_data["es_ins"] = data.get("es_ins", 0)
    ordered_data["is_par"] = data.get("is_par", 0)
    ordered_data["ro_par"] = data.get("ro_par", 0)
    ordered_data["ro_ins"] = data.get("ro_ins", 0)
    ordered_data["wwr"] = data.get("wwr", 0)
    ordered_data["av"] = av_value
    ordered_data["gfa"] = gfa_value

    with open(path, "w") as f:
        json.dump(ordered_data, f, indent=2)

    Rhino.RhinoApp.WriteLine("\u2705 Updated {} with av={} and gfa={} preserving key order.".format(path, av_value, gfa_value))

def compute_total_metrics():
    Rhino.RhinoApp.WriteLine("\ud83d\udcca Computing total geometry metrics...")
    breps = []
    for obj in sc.doc.Objects:
        if not obj.IsValid or not obj.Attributes.Visible:
            continue
        geom = obj.Geometry
        if isinstance(geom, Rhino.Geometry.Extrusion):
            geom = geom.ToBrep()
        if geom and isinstance(geom, Rhino.Geometry.Brep) and geom.IsSolid:
            breps.append(geom)

    if not breps:
        Rhino.RhinoApp.WriteLine("\u26a0\ufe0f No solid Breps found to union.")
        update_compiled_ml_data(gfa_value=0, av_value=0)
        return

    union_result = Rhino.Geometry.Brep.CreateBooleanUnion(breps, sc.doc.ModelAbsoluteTolerance)
    if union_result and len(union_result) > 0:
        Rhino.RhinoApp.WriteLine("\u2705 Boolean union successful. Resulting solids: {}".format(len(union_result)))
        breps = union_result
    else:
        Rhino.RhinoApp.WriteLine("\u26a0\ufe0f Boolean union failed. Falling back to individual Breps.")

    total_volume = 0
    total_face_area = 0
    count = 0

    for brep in breps:
        if not brep.IsSolid:
            continue
        vol = Rhino.Geometry.VolumeMassProperties.Compute(brep)
        if vol:
            total_volume += vol.Volume
        for face in brep.Faces:
            area = Rhino.Geometry.AreaMassProperties.Compute(face)
            if area:
                total_face_area += area.Area
        count += 1

    compactness = round(total_face_area / total_volume, 5) if total_volume > 0 else 0
    gfa = round(total_volume / 3, 3)

    if count == 0:
        Rhino.RhinoApp.WriteLine("\u26a0\ufe0f No valid geometry found after union.")
        return

    payload = {
        "total_volume": round(total_volume, 3),
        "total_face_area": round(total_face_area, 3),
        "compactness": compactness,
        "gfa": gfa
    }

    Rhino.RhinoApp.WriteLine("\u2705 Union-based metrics | Volume: {} | Area: {} | Compactness: {} | GFA: {}".format(
        payload["total_volume"], payload["total_face_area"], compactness, gfa))

    update_compiled_ml_data(payload["gfa"], payload["compactness"])
    post_json(POST_URL, payload)
    save_to_file(payload)

# === EVENT HANDLING ===
def deselect_all():
    for obj in sc.doc.Objects:
        if obj.IsSelected(True):
            obj.Select(False)
    sc.doc.Views.Redraw()

def try_compute_with_geometry(max_attempts=1, wait=1.0):
    attempt = 0
    while attempt < max_attempts:
        time.sleep(wait)
        deselect_all()
        sc.doc.Views.Redraw()
        valid_count = sum(1 for obj in sc.doc.Objects if obj.IsValid and not obj.IsDeleted and obj.Attributes.Visible)
        if valid_count > 0:
            Rhino.RhinoApp.WriteLine("\u2705 Found {} valid objects.".format(valid_count))
            compute_total_metrics()
            return
        else:
            Rhino.RhinoApp.WriteLine("\u23f3 Waiting for geometry... ({}/{})".format(attempt + 1, max_attempts))
            attempt += 1
    Rhino.RhinoApp.WriteLine("\u26a0\ufe0f No valid geometry found after waiting. Updating data with zeros.")
    update_compiled_ml_data(0, 0)

def safe_compute():
    global is_running
    if not listener_active:
        Rhino.RhinoApp.WriteLine("\u274c Listener inactive. Skipping computation.")
        return
    if is_running:
        Rhino.RhinoApp.WriteLine("\u23f3 Computation already in progress.")
        return
    is_running = True
    try:
        try_compute_with_geometry()
    finally:
        is_running = False

def debounce_refresh():
    global debounce_timer
    if debounce_timer and debounce_timer.is_alive():
        Rhino.RhinoApp.WriteLine("\u23f1\ufe0f Debounce active, skipping trigger.")
        return

    def delayed_refresh():
        time.sleep(1)
        if not listener_active:
            Rhino.RhinoApp.WriteLine("\u274c Debounced trigger ignored. Listener is inactive.")
            return
        Rhino.RhinoApp.WriteLine("\ud83d\udd01 Debounced event triggered - computing metrics...")
        safe_compute()

    debounce_timer = threading.Thread(target=delayed_refresh)
    debounce_timer.start()

# === RHINO EVENTS ===
def on_add(sender, e):
    Rhino.RhinoApp.WriteLine("\u2795 Object added.")
    debounce_refresh()

def on_delete(sender, e):
    Rhino.RhinoApp.WriteLine("\u2796 Object deleted.")
    debounce_refresh()

def on_replace(sender, e):
    Rhino.RhinoApp.WriteLine("\u267b\ufe0f Object replaced.")
    debounce_refresh()

def on_modify(sender, e):
    Rhino.RhinoApp.WriteLine("\u270f\ufe0f Object modified.")
    debounce_refresh()

def remove_listeners():
    try: Rhino.RhinoDoc.AddRhinoObject -= on_add
    except: pass
    try: Rhino.RhinoDoc.DeleteRhinoObject -= on_delete
    except: pass
    try: Rhino.RhinoDoc.ReplaceRhinoObject -= on_replace
    except: pass
    try: Rhino.RhinoDoc.ModifyObjectAttributes -= on_modify
    except: pass
    Rhino.RhinoApp.WriteLine("\ud83e\udea9 Removed existing event listeners.")

def setup_listeners():
    remove_listeners()
    Rhino.RhinoDoc.AddRhinoObject += on_add
    Rhino.RhinoDoc.DeleteRhinoObject += on_delete
    Rhino.RhinoDoc.ReplaceRhinoObject += on_replace
    Rhino.RhinoDoc.ModifyObjectAttributes += on_modify
    Rhino.RhinoApp.WriteLine("\ud83c\udfb7 Rhino listener is active and monitoring geometry changes.")

def watch_for_capture_signal():
    def watcher():
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        flag_path = os.path.join(base_dir, "knowledge", "capture_now.txt")
        iterations_folder = os.path.join(base_dir, "knowledge", "iterations")
        last_version = None
        while True:
            if os.path.exists(flag_path):
                try:
                    with open(flag_path, "r") as f:
                        version_name = f.read().strip()
                    if version_name and version_name != last_version:
                        last_version = version_name
                        Rhino.RhinoApp.WriteLine("\ud83d\udd14 Triggered capture for version: {}".format(version_name))
                        capture_viewport(version_name, iterations_folder)
                except Exception as e:
                    Rhino.RhinoApp.WriteLine("\u26a0\ufe0f Error reading flag file: {}".format(e))
            time.sleep(2)
    t = threading.Thread(target=watcher)
    t.setDaemon(True)
    t.start()
    Rhino.RhinoApp.WriteLine("Screenshot watcher thread started.")

# === INIT SCRIPT ===
Rhino.RhinoApp.WriteLine("\ud83d\udea6 Starting Rhino listener script...")
setup_listeners()
compute_total_metrics()
Rhino.RhinoApp.WriteLine("\u2705 Rhino listener initialized and ready.")
watch_for_capture_signal()

def shutdown_listener():
    global listener_active
    listener_active = False
    remove_listeners()
    Rhino.RhinoApp.WriteLine("\u274c Rhino listener stopped.")
    Rhino.RhinoApp.WriteLine("\u2705 Rhino listener shut down.")
