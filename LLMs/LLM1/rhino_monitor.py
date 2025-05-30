import Rhino
import Rhino.Geometry as rg
import time
import threading
import requests
import json

class RhinoMonitor:
    def __init__(self):
        self.monitoring = False
        self.last_object_count = 0
        self.server_url = "http://127.0.0.1:5000"
        
    def start_continuous_monitoring(self):
        """Start monitoring Rhino document changes"""
        self.monitoring = True
        print("👁️  Starting Rhino monitoring...")
        
        while self.monitoring:
            try:
                self.check_for_geometry_changes()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)
    
    def check_for_geometry_changes(self):
        """Check for new geometry and analyze it"""
        try:
            doc = Rhino.RhinoDoc.ActiveDoc
            if not doc:
                return
            
            # Get all Brep objects
            breps = []
            for obj in doc.Objects:
                if isinstance(obj.Geometry, rg.Brep):
                    breps.append(obj.Geometry)
            
            current_count = len(breps)
            
            # If geometry count changed, analyze
            if current_count != self.last_object_count:
                print(f"📐 Geometry changed: {current_count} objects")
                self.last_object_count = current_count
                
                if breps:
                    self.analyze_and_send_geometry(breps)
        
        except Exception as e:
            print(f"Geometry check error: {e}")
    
    def analyze_and_send_geometry(self, breps):
        """Analyze Breps and send data to server"""
        try:
            total_volume = 0
            total_surface_area = 0
            
            for brep in breps:
                volume_props = rg.VolumeMassProperties.Compute(brep)
                area_props = rg.AreaMassProperties.Compute(brep)
                
                if volume_props and area_props:
                    total_volume += volume_props.Volume
                    total_surface_area += area_props.Area
            
            if total_volume > 0:
                # Calculate metrics
                gfa = total_volume / 3.0  # Assuming 3m floor height
                compactness = total_surface_area / total_volume
                
                # Send to server
                data = {
                    "gfa": round(gfa, 2),
                    "av": round(compactness, 4),
                    "timestamp": time.time(),
                    "source": "rhino_monitor",
                    "object_count": len(breps)
                }
                
                self.send_to_server(data)
                print(f"📊 Sent: GFA={gfa:.1f}m², Compactness={compactness:.4f}")
        
        except Exception as e:
            print(f"Analysis error: {e}")
    
    def send_to_server(self, data):
        """Send geometry data to server"""
        try:
            response = requests.post(
                f"{self.server_url}/rhino_data",
                json=data,
                timeout=5
            )
            if response.status_code != 200:
                print(f"Server error: {response.status_code}")
        except Exception as e:
            print(f"Send error: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False