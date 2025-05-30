import os
import sys

print("=== PYTHON PATH FINDER ===")
print("Current Python executable:", sys.executable)
print("Python version:", sys.version)

# Common Python installation paths
possible_paths = [
    "C:\\Python312\\python.exe",
    "C:\\Python311\\python.exe", 
    "C:\\Python310\\python.exe",
    "C:\\Python39\\python.exe",
    "C:\\Users\\joaqu\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
    "C:\\Users\\joaqu\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
    "C:\\Users\\joaqu\\AppData\\Local\\Programs\\Python\\Python310\\python.exe",
    "C:\\Program Files\\Python312\\python.exe",
    "C:\\Program Files\\Python311\\python.exe",
    "C:\\Program Files (x86)\\Python312\\python.exe",
    "python.exe"  # If in PATH
]

print("\n=== CHECKING COMMON PYTHON LOCATIONS ===")
for path in possible_paths:
    if path == "python.exe":
        # Check if python is in PATH
        try:
            import subprocess
            result = subprocess.run(["python", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ FOUND: python.exe (in PATH) - {result.stdout.strip()}")
            else:
                print("❌ python.exe not in PATH")
        except:
            print("❌ python.exe not in PATH")
    else:
        if os.path.exists(path):
            print(f"✅ FOUND: {path}")
        else:
            print(f"❌ Not found: {path}")

print("\n=== CURRENT SCRIPT LOCATION ===")
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Script directory: {script_dir}")

print("\n=== CHECKING FOR gh_server.py ===")
server_path = os.path.join(script_dir, "gh_server.py")
if os.path.exists(server_path):
    print(f"✅ Found gh_server.py at: {server_path}")
else:
    print(f"❌ gh_server.py not found at: {server_path}")
    # Look for it in other locations
    print("Searching for gh_server.py...")
    for root, dirs, files in os.walk(script_dir):
        if "gh_server.py" in files:
            found_path = os.path.join(root, "gh_server.py")
            print(f"✅ FOUND gh_server.py at: {found_path}")

print("\n=== RECOMMENDATION ===")
print("Copy the correct Python path from above and update your main.py file")