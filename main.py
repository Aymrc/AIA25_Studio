# -*- coding: utf-8 -*-
import subprocess
import os
import sys

import Eto.Forms as forms
import Eto.Drawing as drawing
import Rhino.UI
import System
import webbrowser   

# === Rhino Listener Import === NEW
sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
import rhino_listener as listener  # Make sure utils/rhino_listener.py defines `shutdown_listener()`
#================================END

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

def install_requirements_if_needed():
    python_path = get_universal_python_path()
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        print("Checking/installing requirements from requirements.txt...")
        try:
            subprocess.check_call([python_path, "-m", "pip", "install", "-r", req_file])

            print("All requirements installed.")
        except subprocess.CalledProcessError as e:
            print("Failed to install requirements: {}".format(e))
    else:
        print("requirements.txt not found!")

install_requirements_if_needed()

def show_copilot_ui():
    # === Show the Rhino Copilot UI ===

    # === UI window sizes & margins ===
    marginX, marginY = 35, 35
    chatWidth = 550
    chatHeight = 250
    dataWidth = 500
    dataHeight = 600

    screen = Rhino.UI.RhinoEtoApp.MainWindow.Screen
    work_x = screen.WorkingArea.X
    work_y = screen.WorkingArea.Y
    work_w = screen.WorkingArea.Width
    work_h = screen.WorkingArea.Height

    chat_form = None
    data_form = None



    # === Create Chat Window ===
    chat_form = forms.Form()
    chat_form.Title = "Copilot"
    chat_form.ClientSize = drawing.Size(chatWidth, chatHeight)
    chat_form.Topmost = True

    # === icon ===
    icon_path = os.path.abspath("ui/assets/copilot_icon.ico")
    if os.path.exists(icon_path):
        chat_form.Icon = drawing.Icon(icon_path)
    else:
        print("Icon not found at:", icon_path)

    chat_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ui", "chat.html")) # <<< CHAT
    if not os.path.exists(chat_path):
        print("HTML file not found for chat.html:", chat_path)
        return

    chat_web = forms.WebView()
    chat_web.Url = System.Uri("file:///" + chat_path.replace("\\", "/"))
    chat_form.Content = chat_web



    # === Create Data Window ===
    data_form = forms.Form()
    data_form.Title = "Copilot"
    data_form.ClientSize = drawing.Size(dataWidth, dataHeight)
    data_form.Topmost = True

    # === icon ===
    icon_path = os.path.abspath("ui/assets/copilot_icon.ico")
    if os.path.exists(icon_path):
        data_form.Icon = drawing.Icon(icon_path)
    else:
        print("Icon not found at:", icon_path)

    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ui", "data.html")) # <<< DATA
    if not os.path.exists(data_path):
        print("HTML file not found for data.html", data_path)
        return

    data_web = forms.WebView()
    data_web.Url = System.Uri("file:///" + data_path.replace("\\", "/"))
    data_form.Content = data_web

    # === Positioning ===
    chat_x = int(work_x + marginX)
    chat_y = int(work_y + work_h - chatHeight - marginY)

    data_x = int(work_x + work_w - dataWidth - marginX)
    data_y = int(work_y + work_h - dataHeight - marginY)

    chat_form.Location = drawing.Point(chat_x, chat_y)
    data_form.Location = drawing.Point(data_x, data_y)

    # === Close both when one is closed ===
    def close_both(_sender, _event):
        if chat_form and chat_form.Visible:
            chat_form.Close()
        if data_form and data_form.Visible:
            data_form.Close()

    #================= Shutdown Rhino listener=============
    try:
        listener.shutdown_listener()
        print("✅ Rhino listener shut down.")
    except Exception as ex:
        print("⚠️ Error shutting down listener:", ex)
    #===================================================END

    chat_form.Closed += close_both
    data_form.Closed += close_both

    # === Show windows ===
    chat_form.Show()
    data_form.Show()
    
def start_backend():
    # Start the backend server
    print("Starting Rhino Copilot backend...")

    #============= Force chat server to use port 5001 (needed by frontend)
    os.environ["COPILOT_PORT"] = "5001"
    #========================================END

    # Double check that PORT is used
    # webbrowser.open("http://localhost:5001")
 
    # Get script-relative paths (works regardless of working directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(script_dir, "server", "chat_server.py")
    python_path = get_universal_python_path() #universal vs python3

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
        print("Make sure server/chat_server.py exists in your project directory")
        return False

    # Start server with proper working directory
    try:
        # subprocess.Popen([python_path, server_path], creationflags=0, cwd=script_dir)
        # log = os.path.join(script_dir, "backend_launch.log")
        print("Current script_dir:", script_dir) # debug print
        print("Server path:", server_path)
        print("Python path:", python_path)
        print("LLMCALLS location expected at:", os.path.join(os.path.dirname(script_dir), "llm_calls.py"))
        print("Setting working directory to:", os.path.dirname(script_dir))
        project_root = os.path.dirname(os.path.abspath(__file__))
        server_path = os.path.join(project_root, "server", "chat_server.py")

        subprocess.Popen(
            [python_path, "-m", "server.chat_server"],
            creationflags=0,
            cwd=project_root
        )

        #=== Start WebApp server
        webapp_server_path = os.path.join(script_dir, "server", "webapp_server.py")
        if os.path.exists(webapp_server_path):
            print("🚀 Launching WebApp server on port 5002...")
            subprocess.Popen(
                [python_path, webapp_server_path],
                cwd=script_dir,
                creationflags=0,#subprocess.CREATE_NO_WINDOW,  # optional: hides terminal
            )
        else:
            print("WebApp server not found at:", webapp_server_path)


        # === Start geometry receiver on port 5060 ============================NEW
        receiver_path = os.path.join(script_dir, "utils", "rhino_receiver.py")
        if os.path.exists(receiver_path):
            print("✅ Launching Rhino geometry receiver...")
            subprocess.Popen(
                [python_path, receiver_path],
                creationflags=0, #subprocess.CREATE_NO_WINDOW, #0 to get terminal back
                cwd=script_dir
            )
        else:
            print("⚠️ Rhino receiver script not found at:", receiver_path)

        #======================================================================END


        print("Backend server started successfully!")
        print("Server should be available at: http://localhost:5001")
        return True
        
    except Exception as e:
        print("Error starting backend: " + str(e))
        print("")
        print("Common fixes:")
        print("1. Install required packages:")
        print("   " + str(python_path) + " -m pip install flask requests openai")
        print("2. Check Windows Defender/Antivirus settings")
        print("3. Run Rhino as Administrator")
        return False, python_path

def launch_copilot():
    # Universal launcher that works for any Rhino user
    print("=" * 60)
    print("RHINO COPILOT - UNIVERSAL LAUNCHER")
    print("=" * 60)
    print("User: " + str(os.getenv('USERNAME', 'Unknown')))
    print("Script: " + str(__file__))
    print("")
    
    # Step 1: Start backend
    backend_started = start_backend()
    
    if backend_started:
        #rhino_listener()

        print("Waiting for server to initialize...")
        import time
        time.sleep(2)
        
        # Step 2: Show UI
        ui_loaded = show_copilot_ui()
        
        if ui_loaded:
            print("SUCCESS: Rhino Copilot launched!")
        else:
            print("Backend running, but UI failed to load")
            print("You can still access the server at: http://localhost:5001")
    else:
        print("FAILED: Could not start backend server")
        print("Please check the error messages above")


launch_copilot()