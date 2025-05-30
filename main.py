# -*- coding: utf-8 -*-
import subprocess
import os
import webbrowser

import Eto.Forms as forms
import Eto.Drawing as drawing
import Rhino.UI
import System
import os



def show_copilot_ui():
    dialog = forms.Form()
    dialog.Title = "Rhino Copilot" # Check COpilot name / How are we calling it?
    dialog.ClientSize = drawing.Size(600, 1000)
    dialog.Topmost = True

    web_view = forms.WebView()

    html_path = os.path.abspath("UI/index.html")
    uri = System.Uri("file:///" + html_path.replace("\\", "/"))

    web_view.Url = uri
    dialog.Content = web_view
    dialog.Show()


#  === Starts the server for LM Studio ===
def start_backend():
    server_path = os.path.abspath("SERVER/chat_server.py")

    # Use your own installed Python
    python_path = "C:\Python312\python.exe"

    subprocess.Popen([python_path, server_path], creationflags=0)


# === This starts the UI ===
def launch_copilot():
    start_backend()
    show_copilot_ui()
    print("LLM server started")

    print("Launching Copilot...")
    # webbrowser.open("UI\index.html")

launch_copilot()




# === This starts the Copilot ===
def launch():
    print("launchCopilot.py is running ...")
    print("Checking for script path...")
    
    python_path = "C:\Python312\python.exe" # this makes sure Rhino uses Python3 instead of iron python 
    script_path = "/SERVER/chat_server.py" # here, place the python scripts you want to run


    if os.path.exists(python_path) and os.path.exists(script_path):
        subprocess.Popen([python_path, script_path], creationflags=0)
    else:
        print("File not found")
        print(" - Python path:", python_path)
        print(" - Script path:", script_path)

launch()