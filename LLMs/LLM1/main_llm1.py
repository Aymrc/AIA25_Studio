# -*- coding: utf-8 -*-
import subprocess
import os
import sys

import Eto.Forms as forms
import Eto.Drawing as drawing
import Rhino.UI
import System

def get_universal_python_path():
    """Universal Python detection that works for ANY user on ANY system"""
    
    # Method 1: Use current Python interpreter (most reliable)
    if sys.executable and os.path.exists(sys.executable):
        print("Using current Python: " + str(sys.executable))
        return sys.executable
    
    # Method 2: Dynamic user detection
    username = os.getenv('USERNAME', 'Unknown')
    print("Detecting Python for user: " + str(username))
    
    # All possible Python versions and locations
    python_versions = ['313', '312', '311', '310', '39', '38']
    
    # User-specific installation paths
    user_base_paths = [
        r"C:\Users\{}\AppData\Local\Programs\Python\Python{}\python.exe",
        r"C:\Users\{}\AppData\Local\Microsoft\WindowsApps\python.exe",
        r"C:\Users\{}\Anaconda3\python.exe",
        r"C:\Users\{}\Miniconda3\python.exe",
        r"C:\Users\{}\miniconda3\python.exe",
        r"C:\Users\{}\anaconda3\python.exe",
    ]
    
    # Try user-specific paths
    for base_path in user_base_paths:
        if '{}' in base_path and 'Python{}' in base_path:
            # For versioned Python paths
            for version in python_versions:
                path = base_path.format(username, version)
                if os.path.exists(path):
                    print("Found user Python: " + str(path))
                    return path
        else:
            # For non-versioned paths
            path = base_path.format(username)
            if os.path.exists(path):
                print("Found user Python: " + str(path))
                return path
    
    # Method 3: System-wide installations
    system_paths = []
    for version in python_versions:
        system_paths.extend([
            r"C:\Python{}\python.exe".format(version),
            r"C:\Program Files\Python{}\python.exe".format(version),
            r"C:\Program Files (x86)\Python{}\python.exe".format(version),
        ])
    
    # Add common system paths
    system_paths.extend([
        r"C:\ProgramData\Anaconda3\python.exe",
        r"C:\ProgramData\Miniconda3\python.exe",
        r"C:\Anaconda3\python.exe",
        r"C:\Miniconda3\python.exe",
    ])
    
    for path in system_paths:
        if os.path.exists(path):
            print("Found system Python: " + str(path))
            return path
    
    # Method 4: Search system PATH
    print("Searching system PATH...")
    for python_cmd in ['python', 'python3', 'py']:
        try:
            result = subprocess.run(['where', python_cmd], 
                                  capture_output=True, text=True, shell=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                paths = result.stdout.strip().split('\n')
                for path in paths:
                    path = path.strip()
                    if os.path.exists(path) and 'python.exe' in path.lower():
                        print("Found PATH Python: " + str(path))
                        return path
        except:
            continue
    
    # Method 5: Try py launcher (Windows Python Launcher)
    try:
        result = subprocess.run(['py', '-c', 'import sys; print(sys.executable)'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip()
            if os.path.exists(path):
                print("Found via py launcher: " + str(path))
                return path
    except:
        pass
    
    print("No Python installation found!")
    return None

def show_copilot_ui():
    """Show the Rhino Copilot UI"""
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
        return True
    else:
        print("HTML file not found: " + str(html_path))
        return False

def start_backend():
    """Start the backend server"""
    print("Starting Rhino Copilot backend...")
    
    # Get script-relative paths (works regardless of working directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "SERVER", "chat_server.py")
    python_path = get_universal_python_path()
    
    print("Script directory: " + str(script_dir))
    print("Server path: " + str(server_path))
    print("Python path: " + str(python_path))
    print("Current user: " + str(os.getenv('USERNAME', 'Unknown')))

    # Validate paths
    if not python_path:
        print("ERROR: No Python executable found!")
        print("")
        print("SOLUTION:")
        print("1. Install Python from: https://www.python.org/downloads/")
        print("2. During installation, check 'Add Python to PATH'")
        print("3. Restart Rhino after installation")
        return False
        
    if not os.path.exists(python_path):
        print("Python executable not found: " + str(python_path))
        return False
        
    if not os.path.exists(server_path):
        print("Server script not found: " + str(server_path))
        print("Make sure SERVER/chat_server.py exists in your project directory")
        return False

    # Start server with proper working directory
    try:
        subprocess.Popen([python_path, server_path], creationflags=0, cwd=script_dir)
        print("Backend server started successfully!")
        print("Server should be available at: http://localhost:5000")
        return True
        
    except Exception as e:
        print("Error starting backend: " + str(e))
        print("")
        print("Common fixes:")
        print("1. Install required packages:")
        print("   " + str(python_path) + " -m pip install flask requests openai")
        print("2. Check Windows Defender/Antivirus settings")
        print("3. Run Rhino as Administrator")
        return False

def launch_copilot():
    """Universal launcher that works for any Rhino user"""
    print("=" * 60)
    print("RHINO COPILOT - UNIVERSAL LAUNCHER")
    print("=" * 60)
    print("User: " + str(os.getenv('USERNAME', 'Unknown')))
    print("Script: " + str(__file__))
    print("")
    
    # Step 1: Start backend
    backend_started = start_backend()
    
    if backend_started:
        print("Waiting for server to initialize...")
        import time
        time.sleep(2)
        
        # Step 2: Show UI
        ui_loaded = show_copilot_ui()
        
        if ui_loaded:
            print("SUCCESS: Rhino Copilot launched!")
        else:
            print("Backend running, but UI failed to load")
            print("You can still access the server at: http://localhost:5000")
    else:
        print("FAILED: Could not start backend server")
        print("Please check the error messages above")

def launch():
    """Legacy compatibility function"""
    launch_copilot()

# Main execution - works for any user
launch_copilot()