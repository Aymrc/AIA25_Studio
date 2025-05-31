# -*- coding: utf-8 -*-
import subprocess
import os
import sys

import Eto.Forms as forms
import Eto.Drawing as drawing
import Rhino.UI
import System

def get_universal_python_path():
    """
    Universal Python detection that works for ANY user
    Priority: sys.executable > user-specific > system-wide > manual
    """
    username = os.getenv('USERNAME', 'Unknown')
    
    # Method 1: Use current Python (most reliable in Rhino)
    if sys.executable and os.path.exists(sys.executable):
        print("Found Python via sys.executable: " + str(sys.executable))
        return sys.executable
    
    # Method 2: User-specific installations (works for joaqu, cesar, anyone)
    user_paths = [
        # Standard user Python installations
        r"C:\Users\{}\AppData\Local\Programs\Python\Python313\python.exe".format(username),
        r"C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe".format(username),
        r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(username),
        r"C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe".format(username),
        
        # Microsoft Store Python
        r"C:\Users\{}\AppData\Local\Microsoft\WindowsApps\python.exe".format(username),
        
        # Anaconda/Miniconda
        r"C:\Users\{}\Anaconda3\python.exe".format(username),
        r"C:\Users\{}\Miniconda3\python.exe".format(username),
    ]
    
    for path in user_paths:
        if os.path.exists(path):
            print("Found user Python: " + str(path))
            return path
    
    # Method 3: System-wide installations
    system_paths = [
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe", 
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",
        r"C:\ProgramData\Anaconda3\python.exe",
        r"C:\ProgramData\Miniconda3\python.exe",
    ]
    
    for path in system_paths:
        if os.path.exists(path):
            print("Found system Python: " + str(path))
            return path
    
    # Method 4: Rhino Python (if available)
    rhino_paths = [
        r"C:\Program Files\Rhino 8\System\python.exe",
        r"C:\Program Files\Rhino 7\System\python.exe",
        r"C:\Program Files (x86)\Rhino 8\System\python.exe",
        r"C:\Program Files (x86)\Rhino 7\System\python.exe",
    ]
    
    for path in rhino_paths:
        if os.path.exists(path):
            print("Found Rhino Python: " + str(path))
            return path
    
    # Method 5: Search PATH
    try:
        result = subprocess.run(['where', 'python'], capture_output=True, text=True, shell=True)
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip().split('\n')[0]
            if os.path.exists(path):
                print("Found Python in PATH: " + str(path))
                return path
    except:
        pass
    
    print("No Python executable found!")
    return None

def show_copilot_ui():
    dialog = forms.Form()
    dialog.Title = "Rhino Copilot"
    dialog.ClientSize = drawing.Size(600, 1000)
    dialog.Topmost = True

    web_view = forms.WebView()

    # Always use script-relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, "UI", "index.html")
    
    print("Looking for HTML at: " + str(html_path))
    
    if os.path.exists(html_path):
        uri = System.Uri("file:///" + html_path.replace("\\", "/"))
        web_view.Url = uri
        dialog.Content = web_view
        dialog.Show()
        print("UI loaded successfully!")
    else:
        print("HTML file not found: " + str(html_path))

def start_backend():
    print("Starting Rhino Copilot backend...")
    
    # Get script-relative paths (works regardless of working directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "SERVER", "chat_server.py")
    python_path = get_universal_python_path()
    
    print("Script directory: " + str(script_dir))
    print("Server path: " + str(server_path))
    print("Python path: " + str(python_path))
    print("Current user: " + str(os.getenv('USERNAME', 'Unknown')))

    # Validate everything
    if not python_path:
        print("CRITICAL: No Python executable found!")
        print("")
        print("SOLUTION: Install Python from https://www.python.org/downloads/")
        print("Make sure to check 'Add Python to PATH' during installation")
        return False
        
    if not os.path.exists(python_path):
        print("Python path does not exist: " + str(python_path))
        return False
        
    if not os.path.exists(server_path):
        print("Server script not found: " + str(server_path))
        print("Make sure SERVER/chat_server.py exists in your project")
        return False

    # Start server with correct working directory
    try:
        subprocess.Popen([python_path, server_path], creationflags=0, cwd=script_dir)
        print("Backend server started successfully!")
        return True
        
    except Exception as e:
        print("Error starting backend: " + str(e))
        return False

def launch_copilot():
    """Universal launcher that works for any user"""
    print("=" * 40)
    print("RHINO COPILOT UNIVERSAL LAUNCHER")
    print("=" * 40)
    print("User: " + str(os.getenv('USERNAME', 'Unknown')))
    print("Script: " + str(__file__))
    print("")
    
    backend_started = start_backend()
    
    if backend_started:
        print("Waiting for server to initialize...")
        import time
        time.sleep(2)
        show_copilot_ui()
        print("SUCCESS: Copilot launched!")
    else:
        print("FAILED: Could not start backend server")
        print("Check error messages above for troubleshooting")

def launch():
    """Legacy compatibility function"""
    launch_copilot()

# Main execution - works whether run directly or imported
if __name__ == "__main__":
    launch_copilot()
else:
    # When run from Rhino button
    launch_copilot()