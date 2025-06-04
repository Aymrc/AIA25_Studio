import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino

import System
import os
import datetime

# call this viewport capture from ML with:
# from UTILS.SaveState_image import capture_viewport


def capture_viewport(version_name, folder): # takes the input "version name" from the calling file
    os.makedirs(folder, exist_ok=True)

    #file name to be similar to the iteration.json
    filename = f"{version_name}.png"
    filepath = os.path.join(folder, filename)

    view = sc.doc.Views.ActiveView
    if not view:
        print("No active view found.")
        return None

    #maybe we will have constrainted width & height? Square? Or not
    width = view.ActiveViewport.Size.Width
    height = view.ActiveViewport.Size.Height
    bitmap = view.CaptureToBitmap(Rhino.Display.ViewCaptureSettings(view, width, height, True))

    if bitmap:
        bitmap.Save(filepath, System.Drawing.Imaging.ImageFormat.Png)
        print(f"Screenshot saved to: {filepath}")
        return filepath
    else:
        print("Failed to capture viewport.")
        return None
