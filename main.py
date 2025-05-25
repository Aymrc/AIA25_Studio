# -*- coding: utf-8 -*-
import subprocess
import os
import webbrowser


#  === Starts the server for LM Studio ===
def start_backend():
    server_path = os.path.abspath("SERVER/chat_server.py")

    # Use your installed Python
    python_path = "C:\Python312\python.exe"

    subprocess.Popen([python_path, server_path], creationflags=0)


# === This starts the UI ===
def launch_copilot():
    start_backend()
    print("LLM server started")

    print("Launching Copilot...")
    webbrowser.open("UI\index.html")

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