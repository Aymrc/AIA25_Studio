# -*- coding: utf-8 -*-
import Rhino
import scriptcontext as sc
import System
import System.Net
import System.Text
import json
import threading
import time

# Track if we're already waiting to recompute
debounce_timer = None

def post_json(url, data):
    try:
        client = System.Net.WebClient()
        client.Headers.Add("Content-Type", "application/json")
        body = System.Text.Encoding.UTF8.GetBytes(json.dumps(data))
        client.UploadData(url, "POST", body)
        print("✅ Posted to server:", data)
    except Exception as e:
        print("❌ Error posting:", e)

def compute_total_metrics():
    total_volume = 0
    total_face_area = 0
    count = 0

    for obj in sc.doc.Objects:
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
            for i in range(geom.Faces.Count):
                total_face_area += geom.Faces.GetFaceArea(i)
            count += 1

    print("📦 Objects processed:", count)
    print("🧮 Total Volume:", round(total_volume, 3))
    print("📐 Total Face Area:", round(total_face_area, 3))

    payload = {
        "total_volume": round(total_volume, 3),
        "total_face_area": round(total_face_area, 3)
    }

    post_json("http://127.0.0.1:5000/rhino_data", payload)

def debounce_refresh():
    global debounce_timer
    if debounce_timer and debounce_timer.is_alive():
        return  # already waiting

    def delayed_refresh():
        time.sleep(1.0)  # wait a second to absorb events
        compute_total_metrics()

    debounce_timer = threading.Thread(target=delayed_refresh)
    debounce_timer.Start()

def on_add(sender, e):
    debounce_refresh()

def on_delete(sender, e):
    debounce_refresh()

def remove_listeners():
    try: Rhino.RhinoDoc.AddRhinoObject -= on_add
    except: pass
    try: Rhino.RhinoDoc.DeleteRhinoObject -= on_delete
    except: pass

def setup_listeners():
    remove_listeners()
    Rhino.RhinoDoc.AddRhinoObject += on_add
    Rhino.RhinoDoc.DeleteRhinoObject += on_delete
    print("👂 Listener active — will debounce total update.")

setup_listeners()
