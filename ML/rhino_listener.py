import rhinoinside
rhinoinside.load()

import Rhino
import scriptcontext as sc
import time
import threading

# === Event handlers ===

def on_add(sender, e):
    print("[Add] Object ID:", e.ObjectId)
    obj = sc.doc.Objects.Find(e.ObjectId)
    if obj:
        print("   Type:", obj.Geometry.ObjectType)

def on_delete(sender, e):
    print("[Delete] Object ID:", e.ObjectId)

def on_replace(sender, e):
    print("[Replace] Object ID:", e.ObjectId)

def add_event_listeners():
    Rhino.RhinoDoc.AddRhinoObject += on_add
    Rhino.RhinoDoc.DeleteRhinoObject += on_delete
    Rhino.RhinoDoc.ReplaceRhinoObject += on_replace
    print("✅ Event listeners registered.")

def keep_alive():
    # Keeps the app running for a while to catch events
    print("🟢 Waiting for Rhino events. Modify geometry in Rhino.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("👋 Shutting down.")
        remove_event_listeners()

def remove_event_listeners():
    Rhino.RhinoDoc.AddRhinoObject -= on_add
    Rhino.RhinoDoc.DeleteRhinoObject -= on_delete
    Rhino.RhinoDoc.ReplaceRhinoObject -= on_replace
    print("❌ Event listeners removed.")

# === Run ===
if __name__ == "__main__":
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    add_event_listeners()
    keep_alive()
