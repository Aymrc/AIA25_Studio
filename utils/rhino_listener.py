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

from Rhino.UI import RhinoEtoApp
from Eto.Forms import Dialog, Label, ImageView, Button, TableLayout, TableRow
from Eto.Drawing import Size, Padding
from Eto.Drawing import Bitmap as EtoBitmap
import scriptcontext as sc
import System.IO
from System.Drawing import Imaging
from System import EventHandler, EventArgs




def show_capture_dialog(show_ui=False):
    import sys
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.append(os.path.join(base_dir, "utils"))

    try:
        from iteration_saver import create_manual_iteration
    except Exception as e:
        Rhino.RhinoApp.WriteLine("Could not import create_manual_iteration(): {}".format(e))
        return

    class SampleEtoViewCaptureDialog(Dialog[bool]):
        def __init__(self):
            self.Title = 'Capture Viewport'
            self.Padding = Padding(10)
            layout = TableLayout(Padding=Padding(10), Spacing=Size(5, 5))
            layout.Rows.Add(self.create_label())
            layout.Rows.Add(self.create_image_view())
            layout.Rows.Add(None)
            layout.Rows.Add(self.create_buttons())
            self.Content = layout

        def create_label(self):
            self.label = Label(Text='Click "Capture" to take screenshot...')
            return self.label

        def create_image_view(self):
            self.image_view = ImageView(Size=Size(300, 200))
            return self.image_view

        def create_buttons(self):
            self.capture_btn = Button(Text='Capture')
            self.capture_btn.Click += System.EventHandler(self.on_capture)

            self.close_btn = Button(Text='Close')
            self.close_btn.Click += System.EventHandler(self.on_close)
            return TableRow(None, self.capture_btn, self.close_btn)

        def on_capture(self, sender=None, e=None):
            try:
                destination_folder = os.path.join(base_dir, "knowledge")
                destination_filename = "ml_output.json"
                json_folder = os.path.join(base_dir, "knowledge", "iterations")

                success, version_id = create_manual_iteration(destination_folder, destination_filename, json_folder)

                if not success:
                    self.label.Text = "Failed to create version: {}".format(version_id)
                    return
                Rhino.RhinoApp.WriteLine("Created new JSON: {}".format(version_id))
            except Exception as ex:
                self.label.Text = "JSON error: {}".format(ex)
                return

            try:
                view = sc.doc.Views.ActiveView
                if not view:
                    self.label.Text = 'No active view.'
                    return

                bmp = view.CaptureToBitmap()
                if bmp:
                    stream = System.IO.MemoryStream()
                    bmp.Save(stream, Imaging.ImageFormat.Png)
                    if stream.Length != 0:
                        self.image_view.Image = Bitmap(stream)
                        self.label.Text = 'Captured view: {}'.format(view.ActiveViewport.Name)
                    stream.Dispose()

                    img_path = os.path.join(base_dir, "knowledge", "iterations", "{}.png".format(version_id))
                    bmp.Save(img_path)
                    Rhino.RhinoApp.WriteLine("Screenshot saved to: {}".format(img_path))
            except Exception as e:
                self.label.Text = "Capture error: {}".format(e)


            # ➕ Save 3DM file
            try:
                model_path = os.path.join(base_dir, "knowledge", "iterations", "{}.3dm".format(version_id))
                opts = Rhino.FileIO.FileWriteOptions()
                doc = Rhino.RhinoDoc.ActiveDoc
                success = doc.Write3dmFile(model_path, opts)
                if success:
                    Rhino.RhinoApp.WriteLine(".3dm file saved: {}".format(model_path))
                else:
                    Rhino.RhinoApp.WriteLine("Failed to save .3dm file.")
            except Exception as e:
                Rhino.RhinoApp.WriteLine("Error saving .3dm file: {}".format(e))

        def on_close(self, sender, e):
            self.Close(True if self.image_view.Image else False)

    if show_ui:
        dlg = SampleEtoViewCaptureDialog()
        dlg.ShowModal(RhinoEtoApp.MainWindow)
    else:
        try:
            destination_folder = os.path.join(base_dir, "knowledge")
            destination_filename = "ml_output.json"
            json_folder = os.path.join(base_dir, "knowledge", "iterations")

            success, version_id = create_manual_iteration(destination_folder, destination_filename, json_folder)

            if not success:
                Rhino.RhinoApp.WriteLine("Could not create version: {}".format(version_id))
                return
            Rhino.RhinoApp.WriteLine("JSON version created: {}".format(version_id))
        except Exception as ex:
            Rhino.RhinoApp.WriteLine("JSON creation error: {}".format(ex))
            return

        try:
            view = sc.doc.Views.ActiveView
            if not view:
                Rhino.RhinoApp.WriteLine("No active view.")
                return
            bmp = view.CaptureToBitmap()
            if bmp:
                img_path = os.path.join(base_dir, "knowledge", "iterations", "{}.png".format(version_id))
                bmp.Save(img_path)
                Rhino.RhinoApp.WriteLine("Screenshot saved to: {}".format(img_path))
        except Exception as e:
            Rhino.RhinoApp.WriteLine("Image capture error: {}".format(e))

        # ➕ Save 3DM file (headless mode)
        try:
            model_path = os.path.join(base_dir, "knowledge", "iterations", "{}.3dm".format(version_id))
            opts = Rhino.FileIO.FileWriteOptions()
            doc = Rhino.RhinoDoc.ActiveDoc
            success = doc.Write3dmFile(model_path, opts)
            if success:
                Rhino.RhinoApp.WriteLine(".3dm file saved: {}".format(model_path))
            else:
                Rhino.RhinoApp.WriteLine("Failed to save .3dm file.")
        except Exception as e:
            Rhino.RhinoApp.WriteLine("Error saving .3dm file: {}".format(e))


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
def save_to_file(data):
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        folder = os.path.join(project_root, "knowledge")
        if not os.path.exists(folder):
            os.makedirs(folder)
        path = os.path.join(folder, "geometry_metrics.json")
        Rhino.RhinoApp.WriteLine("Saving data:\n" + json.dumps(data, indent=2))
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        Rhino.RhinoApp.WriteLine("Metrics saved to: " + path)
    except Exception as e:
        Rhino.RhinoApp.WriteLine("Error saving JSON: " + str(e))

# === MAIN METRICS COMPUTATION ===
def update_compiled_ml_data(volume, compactness, shape_efficiency):
    path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "compiled_ml_data.json")
    with open(path, "r") as f:
        data = json.load(f)

    ordered_data = OrderedDict()
    ordered_data["Typology"] = data.get("Typology", 1)
    ordered_data["WWR"] = data.get("WWR", 3)
    ordered_data["EW_PAR"] = data.get("EW_PAR", 0)
    ordered_data["EW_INS"] = data.get("EW_INS", 0)
    ordered_data["IW_PAR"] = data.get("IW_PAR", 0)
    ordered_data["ES_INS"] = data.get("ES_INS", 0)
    ordered_data["IS_PAR"] = data.get("IS_PAR", 0)
    ordered_data["RO_PAR"] = data.get("RO_PAR", 0)
    ordered_data["RO_INS"] = data.get("RO_INS", 0)
    ordered_data["BC"] = data.get("BC", 2)
    ordered_data["A/V"] = compactness
    ordered_data["Volume(m3)"] = volume
    ordered_data["VOL/VOLBBOX"] = shape_efficiency

    with open(path, "w") as f:
        json.dump(ordered_data, f, indent=2)

    Rhino.RhinoApp.WriteLine("Updated compiled_ml_data.json with Volume(m3)={}, A/V={}, VOL/VOLBBOX={}".format(volume, compactness, shape_efficiency))

def compute_total_metrics():
    sc.doc = Rhino.RhinoDoc.ActiveDoc
    #Rhino.RhinoApp.WriteLine("Computing total geometry metrics...")
    breps = []

    # Ensure "Copilot" layer exists
    copilot_layer_name = "___COPILOT_LAYER"
    copilot_layer_index = sc.doc.Layers.FindByFullPath(copilot_layer_name, True)

    if copilot_layer_index == -1:
        Rhino.RhinoApp.WriteLine("'{}' layer not found. Creating it...".format(copilot_layer_name))
        layer = Rhino.DocObjects.Layer()
        layer.Name = copilot_layer_name
        sc.doc.Layers.Add(layer)
        copilot_layer_index = sc.doc.Layers.FindByFullPath(copilot_layer_name, True)
        if copilot_layer_index == -1:
            Rhino.RhinoApp.WriteLine("Could not create or locate the '{}' layer.".format(copilot_layer_name))
            return
        
    # Collect Breps from the "Copilot" layer only
    breps = []
    for obj in sc.doc.Objects:
        if not obj.IsValid or not obj.Attributes.Visible:
            continue
        if obj.Attributes.LayerIndex != copilot_layer_index:
            continue

        geom = obj.Geometry
        if isinstance(geom, Rhino.Geometry.Extrusion):
            geom = geom.ToBrep()
        if geom and isinstance(geom, Rhino.Geometry.Brep) and geom.IsSolid:
            breps.append(geom)

    if not breps:
        Rhino.RhinoApp.WriteLine("No solid Breps found to union.")
        update_compiled_ml_data(0, 0, 0)
        return

    union_result = Rhino.Geometry.Brep.CreateBooleanUnion(breps, sc.doc.ModelAbsoluteTolerance)
    if union_result and len(union_result) > 0:
        Rhino.RhinoApp.WriteLine("Boolean union successful. Resulting solids: {}".format(len(union_result)))
        breps = union_result
    else:
        Rhino.RhinoApp.WriteLine("Boolean union failed. Falling back to individual Breps.")

    total_volume = 0
    total_face_area = 0
    combined_bbox = None

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

        bbox = brep.GetBoundingBox(True)
        if combined_bbox:
            combined_bbox.Union(bbox)
        else:
            combined_bbox = bbox

    if total_volume == 0 or combined_bbox is None:
        Rhino.RhinoApp.WriteLine("No valid geometry found or invalid bounding box.")
        update_compiled_ml_data(0, 0, 0)
        return

    compactness = round(total_face_area / total_volume, 3)
    bbox_volume = round(combined_bbox.Volume, 3) if combined_bbox.IsValid else 1.0
    shape_efficiency = round(total_volume / bbox_volume, 3) if bbox_volume > 0 else 0.0

    payload = {
        "total_volume": round(total_volume, 3),
        "total_face_area": round(total_face_area, 3),
        "compactness": compactness,
        "bbox_volume": bbox_volume,
        "shape_efficiency": shape_efficiency
    }

    Rhino.RhinoApp.WriteLine("\nFinal Metrics:")
    for k, v in payload.items():
        Rhino.RhinoApp.WriteLine("{}: {}".format(k, v))

    update_compiled_ml_data(total_volume, compactness, shape_efficiency)
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
            Rhino.RhinoApp.WriteLine("Found {} valid objects.".format(valid_count))
            compute_total_metrics()
            return
        else:
            Rhino.RhinoApp.WriteLine(" Waiting for geometry... ({}/{})".format(attempt + 1, max_attempts))
            attempt += 1
    Rhino.RhinoApp.WriteLine("No valid geometry found after waiting. Updating data with zeros.")
    update_compiled_ml_data(0, 0)

def safe_compute():
    global is_running
    if not listener_active:
        Rhino.RhinoApp.WriteLine("Listener inactive. Skipping computation.")
        return
    if is_running:
        Rhino.RhinoApp.WriteLine("Computation already in progress.")
        return
    is_running = True
    try:
        try_compute_with_geometry()
    finally:
        is_running = False

def debounce_refresh():
    global debounce_timer
    if debounce_timer and debounce_timer.is_alive():
        Rhino.RhinoApp.WriteLine("Debounce active, skipping trigger.")
        return

    def delayed_refresh():
        time.sleep(1)
        if not listener_active:
            Rhino.RhinoApp.WriteLine("Debounced trigger ignored. Listener is inactive.")
            return
        Rhino.RhinoApp.WriteLine("Debounced event triggered - computing metrics...")
        safe_compute()

    debounce_timer = threading.Thread(target=delayed_refresh)
    debounce_timer.start()

# === RHINO EVENTS ===
def on_add(sender, e):
    Rhino.RhinoApp.WriteLine("Object added.")
    debounce_refresh()

def on_delete(sender, e):
    Rhino.RhinoApp.WriteLine("Object deleted.")
    debounce_refresh()

def on_replace(sender, e):
    Rhino.RhinoApp.WriteLine("Object replaced.")
    debounce_refresh()

def on_modify(sender, e):
    Rhino.RhinoApp.WriteLine("Object modified.")
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
    Rhino.RhinoApp.WriteLine("Removed existing event listeners.")

def setup_listeners():
    remove_listeners()
    Rhino.RhinoDoc.AddRhinoObject += on_add
    Rhino.RhinoDoc.DeleteRhinoObject += on_delete
    Rhino.RhinoDoc.ReplaceRhinoObject += on_replace
    Rhino.RhinoDoc.ModifyObjectAttributes += on_modify
    Rhino.RhinoApp.WriteLine("Rhino listener is active and monitoring geometry changes.")


def watch_for_dialog_signal():
    def safe_show_dialog(sender=None, args=None):
        try:
            show_capture_dialog()
        except Exception as e:
            Rhino.RhinoApp.WriteLine("Dialog error: {}".format(e))

    def watcher():
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        flag_path = os.path.join(base_dir, "knowledge", "show_dialog.flag")
        last_trigger_time = 0

        while True:
            if os.path.exists(flag_path):
                try:
                    if time.time() - last_trigger_time > 1:
                        last_trigger_time = time.time()
                        os.remove(flag_path)
                        Rhino.RhinoApp.WriteLine("Triggered Eto viewport capture dialog.")

                        # ✅ Correct delegate usage
                        Rhino.RhinoApp.InvokeOnUiThread(System.Action(safe_show_dialog))

                except Exception as e:
                    Rhino.RhinoApp.WriteLine("Error launching dialog: {}".format(e))
            time.sleep(1)

    t = threading.Thread(target=watcher)
    t.setDaemon(True)
    t.start()
    Rhino.RhinoApp.WriteLine("Dialog watcher thread started.")




# === INIT SCRIPT ===
Rhino.RhinoApp.WriteLine("Starting Rhino listener script...")
setup_listeners()
compute_total_metrics()
Rhino.RhinoApp.WriteLine("Rhino listener initialized and ready.")
#watch_for_capture_signal()
watch_for_dialog_signal()


def shutdown_listener():
    global listener_active
    listener_active = False
    remove_listeners()
    Rhino.RhinoApp.WriteLine("Rhino listener stopped.")
    Rhino.RhinoApp.WriteLine("Rhino listener shut down.")
