"""
SIMPLE RHINO MONITOR - No Rhino.Inside needed
Just monitors Grasshopper's temporary output files that already exist

File: rhino_monitor.py
Run: python rhino_monitor.py
"""

import time
import requests
import os
import tempfile
import json
from datetime import datetime

class SimpleRhinoMonitor:
    """Simple monitor that watches for any signs of Rhino activity"""
    
    def __init__(self):
        self.running = False
        self.server_url = "http://127.0.0.1:5000"
        self.poll_interval = 2.0
        
        # State tracking
        self.last_detection_time = 0
        self.detection_count = 0
        
        # Look for common Grasshopper temp files
        self.temp_dir = tempfile.gettempdir()
        self.watch_patterns = [
            "gh_geometry_*.json",
            "grasshopper_*.tmp", 
            "rhino_*.tmp"
        ]
        
    def check_grasshopper_activity(self):
        """Check if Grasshopper is creating any temp files (indicates Rhino activity)"""
        try:
            current_time = time.time()
            
            # Look for any recently modified files in temp directory
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if any(pattern in file.lower() for pattern in ['grasshopper', 'rhino', 'gh_']):
                        file_path = os.path.join(root, file)
                        try:
                            mod_time = os.path.getmtime(file_path)
                            # If file modified in last 10 seconds
                            if current_time - mod_time < 10:
                                return True, f"Recent activity in {file}"
                        except:
                            continue
            
            return False, "No recent temp file activity"
            
        except Exception as e:
            return False, f"Check error: {str(e)}"
    
    def simple_activity_detection(self):
        """Ultra-simple detection: assume any call means activity"""
        current_time = time.time()
        
        # If this function is called, assume there's activity
        time_since_last = current_time - self.last_detection_time
        
        if time_since_last > 5:  # At least 5 seconds between detections
            self.last_detection_time = current_time
            self.detection_count += 1
            return True, f"Activity detected #{self.detection_count}"
        
        return False, f"Too recent ({time_since_last:.1f}s ago)"
    
    def create_test_activity(self):
        """Create a test file to simulate activity"""
        try:
            test_file = os.path.join(self.temp_dir, "rhino_activity_test.json")
            
            activity_data = {
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "test_activity": True,
                "detection_count": self.detection_count
            }
            
            with open(test_file, 'w') as f:
                json.dump(activity_data, f, indent=2)
            
            print(f"📄 Created test activity file: {test_file}")
            return True, "Test activity created"
            
        except Exception as e:
            return False, f"Test creation error: {str(e)}"
    
    def notify_server_about_activity(self, reason):
        """Notify Flask server about detected activity"""
        try:
            payload = {
                "self_modeling": True,
                "source": "simple_rhino_monitor",
                "reason": reason,
                "timestamp": time.time(),
                "detection_method": "activity_monitoring"
            }
            
            response = requests.post(
                f"{self.server_url}/set_self_modeling",
                json=payload,
                timeout=3
            )
            
            if response.status_code == 200:
                print(f"✅ Server notified: {reason}")
                return True
            else:
                print(f"❌ Server error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Server notification failed: {str(e)}")
            return False
    
    def monitoring_loop(self):
        """Simple monitoring loop"""
        print("🔄 Starting simple activity monitoring...")
        print(f"🔗 Server URL: {self.server_url}")
        print(f"📁 Temp directory: {self.temp_dir}")
        print("⌨️  Press Ctrl+C to stop")
        print("🧪 This will create test activity every 10 seconds")
        
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                current_time = time.time()
                
                print(f"\n[Cycle {cycle_count}] Checking for activity...")
                
                # Method 1: Check for real Grasshopper activity
                has_gh_activity, gh_status = self.check_grasshopper_activity()
                
                # Method 2: Create test activity every 10 seconds
                should_test = (cycle_count % 5 == 0)  # Every 5 cycles = ~10 seconds
                
                if has_gh_activity:
                    print(f"🎯 REAL ACTIVITY DETECTED: {gh_status}")
                    self.notify_server_about_activity(f"Grasshopper activity: {gh_status}")
                    
                elif should_test:
                    print("🧪 Creating test activity...")
                    test_success, test_msg = self.create_test_activity()
                    
                    if test_success:
                        has_activity, activity_reason = self.simple_activity_detection()
                        if has_activity:
                            print(f"🎯 TEST ACTIVITY: {activity_reason}")
                            self.notify_server_about_activity(f"Test activity: {activity_reason}")
                
                else:
                    print("⏸️ No activity detected")
                
                # Wait before next check
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {str(e)}")
        finally:
            self.running = False
            print("📴 Simple monitoring stopped")
    
    def start(self):
        """Start monitoring"""
        self.monitoring_loop()

def test_server_connection():
    """Test if Flask server is running with detailed debugging"""
    try:
        print("🔍 Testing server connection...")
        print(f"🔗 Trying to connect to: http://127.0.0.1:5000")
        
        response = requests.get("http://127.0.0.1:5000/", timeout=5)
        print(f"📡 Response status: {response.status_code}")
        print(f"📄 Response content: {response.text[:100]}...")
        
        if response.status_code == 200:
            return True, f"Flask server is running (status: {response.status_code})"
        else:
            return False, f"Server responded with status: {response.status_code}"
            
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection refused - server not running on port 5000: {str(e)}"
    except requests.exceptions.Timeout as e:
        return False, f"Connection timeout: {str(e)}"
    except Exception as e:
        return False, f"Server connection failed: {str(e)}"

if __name__ == "__main__":
    print("="*50)
    print("🔍 SIMPLE RHINO ACTIVITY MONITOR")
    print("="*50)
    print("Monitors for Rhino/Grasshopper activity")
    print("Creates test notifications for your LLM system")
    print("="*50)
    
    # Test server connection
    print("🧪 Testing server connection first...")
    server_ok, server_msg = test_server_connection()
    print(f"🔗 Server test result: {server_msg}")
    
    if server_ok:
        print("✅ Server connection confirmed - starting monitor")
    else:
        print("⚠️  Server issue detected but continuing anyway...")
        print("💡 Make sure gh_server.py is running on port 5000")
    
    print("\n🚀 FORCING monitor to start regardless...")
    print("📊 You should see activity detection every 10 seconds")
    print("🛑 Press Ctrl+C to stop\n")
    
    monitor = SimpleRhinoMonitor()
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")
    except Exception as e:
        print(f"❌ Monitor error: {str(e)}")

"""
SIMPLE SETUP:

1. Save this as: rhino_monitor.py
2. Run in VSCode terminal: python rhino_monitor.py  
3. It will create test activity and notify your server
4. No Rhino.Inside, no complex setup needed!

This gives you the foundation to test server notifications.
Once this works, we can enhance it to detect real Rhino activity.
"""