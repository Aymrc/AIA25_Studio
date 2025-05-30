import subprocess
import os
import webbrowser

try:
    import Eto.Forms as forms
    import Eto.Drawing as drawing
    import Rhino.UI
    import System
    ETO_AVAILABLE = True
except ImportError:
    ETO_AVAILABLE = False

def show_copilot_ui():
    if not ETO_AVAILABLE:
        print("Eto forms not available - running server only")
        return
        
    dialog = forms.Form()
    dialog.Title = "Rhino Copilot"
    dialog.ClientSize = drawing.Size(600, 1000)
    dialog.Topmost = True

    web_view = forms.WebView()

    html_path = os.path.abspath("UI/index.html")
    uri = System.Uri("file:///" + html_path.replace("\\", "/"))

    web_view.Url = uri
    dialog.Content = web_view
    dialog.Show()

def start_backend():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "gh_server.py")

    python_path = "C:\\Python312\\python.exe"

    if not os.path.exists(python_path):
        print("Python not found at:", python_path)
        return False
        
    if not os.path.exists(server_path):
        print("Server script not found at:", server_path)
        return False

    try:
        subprocess.Popen([python_path, server_path], 
                        cwd=script_dir,
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("Server started successfully!")
        return True
    except Exception as e:
        print("Error starting server:", str(e))
        return False

def launch_copilot():
    print("Starting Rhino Copilot...")
    
    if start_backend():
        print("LLM server started")
        if ETO_AVAILABLE:
            show_copilot_ui()
        else:
            print("Server running at http://127.0.0.1:5000")
    else:
        print("Failed to start server")

def launch():
    print("launchCopilot.py is running...")
    print("Checking for script path...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    python_path = "C:\\Python312\\python.exe"
    script_path = os.path.join(script_dir, "gh_server.py")

    if os.path.exists(python_path) and os.path.exists(script_path):
        subprocess.Popen([python_path, script_path], 
                        cwd=script_dir,
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("Server launched successfully")
    else:
        print("File not found")
        print(" - Python path:", python_path)
        print(" - Script path:", script_path)

# Main execution
launch_copilot()
launch()