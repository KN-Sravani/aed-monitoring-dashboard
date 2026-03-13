import http.server
import socketserver
import json
import numpy as np

try:
    import pandas as pd
    import mysql.connector
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("WARNING: pandas or mysql-connector not found. Using fallback data.")

PORT = 8000

class AEDRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/data'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            df = None
            if PANDAS_AVAILABLE:
                try:
                    db = mysql.connector.connect(
                        host="localhost",
                        user="root",
                        password="Nsravani@123",
                        database="aed_system"
                    )
                    query = "SELECT * FROM aed_data ORDER BY timestamp DESC"
                    df = pd.read_sql(query, db)
                except Exception as e:
                    print(f"MySQL Error: {e}. Using mock data fallback.")

            # Fallback to Mock Data if no DB or no pandas
            if df is None or df.empty:
                import random
                import datetime

                devices = []
                locations = ["Mall", "Airport", "School", "Metro Station", "Corporate Park", "Stadium", "ICU Hospital"]
                statuses = ["active", "active", "active", "emergency", "maintenance"]
                
                for i, loc in enumerate(locations): # Exactly 7 devices
                    device_id = f"AED-{i+1:03d}"
                    stat = random.choice(statuses)
                    batt = random.randint(10, 100)
                    hr = random.randint(40, 150) if stat != "maintenance" else 0
                    
                    devices.append({
                        "device_id": device_id,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "location": loc,
                        "status": stat,
                        "battery_level": batt,
                        "heart_rate_detected": hr
                    })
                
                if PANDAS_AVAILABLE:
                    df = pd.DataFrame(devices)
                else:
                    # Pure python fallback simulation
                    location_coords = {
                        "Mall": [12.9716, 77.5946],             # UB City / MG Road
                        "Airport": [13.1986, 77.7066],          # KIAL Airport
                        "School": [12.9352, 77.6245],           # Koramangala
                        "Metro Station": [12.9784, 77.6408],    # Indiranagar Metro
                        "Corporate Park": [12.9259, 77.6229],   # Electronic City / Tech Park
                        "Stadium": [12.9830, 77.5973],          # Chinnaswamy Stadium
                        "ICU Hospital": [12.9340, 77.6100]      # NIMHANS / Apollo
                    }
                    for d in devices:
                        d["suspicious_message_rate"] = random.randint(0, 100)
                        d["packet_delay"] = random.randint(50, 5000)
                        d["unauthorized_access"] = random.choice([True, False])
                        
                        score = 100
                        if d["status"] == "emergency": score -= 40
                        if d["battery_level"] < 30: score -= 30
                        if d["heart_rate_detected"] > 120 or d["heart_rate_detected"] < 50: score -= 20
                        if d["suspicious_message_rate"] > 50: score -= 15
                        if d["packet_delay"] > 3000: score -= 10
                        if d["unauthorized_access"]: score -= 25
                        
                        d["trust_score"] = max(score, 0)
                        
                        if d["trust_score"] > 80: d["device_health"] = "Safe"
                        elif d["trust_score"] > 50: d["device_health"] = "Warning"
                        else: d["device_health"] = "Risk"
                        
                        d["drift_detected"] = (d["heart_rate_detected"] > 120 or d["heart_rate_detected"] < 50 or d["battery_level"] < 20)
                        
                        coords = location_coords.get(d["location"], [12.9716, 77.5946])
                        # Add a small random jitter to coordinates so points don't stack up exactly
                        jittered_lat = coords[0] + (random.uniform(-0.02, 0.02))
                        jittered_lon = coords[1] + (random.uniform(-0.02, 0.02))
                        d["lat"] = jittered_lat
                        d["lon"] = jittered_lon
                        
                    self.wfile.write(json.dumps(devices).encode('utf-8'))
                    return
            
            # If pandas is available
            df["suspicious_message_rate"] = np.random.randint(0,100,len(df))
            df["packet_delay"] = np.random.randint(50,5000,len(df))
            df["unauthorized_access"] = np.random.choice([True,False],len(df))
            df["policy_violation"] = np.random.choice([0, 1], p=[0.9, 0.1], size=len(df)) # e.g. Fake TLS, unapproved cloud
            df["firmware_drift"] = np.random.choice([0, 1], p=[0.85, 0.15], size=len(df))
            
            # Context-Aware Intelligence
            location_context = {
                "Mall": {"criticality": 1.2, "exposure": 1.5},
                "Airport": {"criticality": 1.3, "exposure": 1.8},
                "School": {"criticality": 1.4, "exposure": 1.2},
                "Metro Station": {"criticality": 1.1, "exposure": 1.6},
                "Corporate Park": {"criticality": 1.2, "exposure": 1.1},
                "Stadium": {"criticality": 1.0, "exposure": 1.9},
                "ICU Hospital": {"criticality": 2.0, "exposure": 1.0} # Added high criticality location
            }
            
            # We keep the assigned locations from the fallback data
            # extended_locations = list(location_context.keys())
            # df["location"] = [np.random.choice(extended_locations) for _ in range(len(df))]
            
            def calculate_trust_and_reasons(row):
                # Trust Score = 100 - Risk Indicators
                # Base Risk weights:
                # Policy violation (30%), Anomaly score (25%), Behavior drift (15%), 
                # Unknown communication (15%), Reporting issues (10%), Fleet correlation (5%)
                
                risk_score = 0
                reasons = []
                drift_type = "None"
                ml_model = ""
                
                # 1. Policy Violation (30%) - Fake TLS, unauthorized cloud
                if row["unauthorized_access"] or row["policy_violation"]:
                    risk_score += 30
                    reasons.append("Policy Violation (Unauthorized Access/Fake TLS)")
                
                # 2. Anomaly Score (25%) - High Ping / Msg Rate
                if row["suspicious_message_rate"] > 50:
                    risk_score += 15
                    reasons.append(f"Network Anomaly: High Msg Rate ({row['suspicious_message_rate']})")
                if row["packet_delay"] > 3000:
                    risk_score += 10
                    reasons.append(f"Network Anomaly: High Ping ({row['packet_delay']}ms)")
                    
                # 3. Reporting Issues (10%) - Battery, Hardware faults
                if row["battery_level"] < 30:
                    risk_score += 10
                    reasons.append(f"Operational Problem: Low Battery ({row['battery_level']}%)")
                    
                # 4. Behavior Drift (15%) - HR completely wrong or firmware changed
                is_hr_drift = row["heart_rate_detected"] > 120 or row["heart_rate_detected"] < 50
                if is_hr_drift and row["heart_rate_detected"] > 0:
                    risk_score += 10
                    reasons.append(f"Telemetry Anomaly: Abnormal HR ({row['heart_rate_detected']} bpm)")
                if row["firmware_drift"]:
                    risk_score += 5
                    reasons.append("Firmware Drift Detected")
                    
                # Set Drift Types and ML Labels based on the above
                drift_chance = np.random.random()
                if is_hr_drift or row["firmware_drift"]:
                    if drift_chance < 0.25:
                        drift_type = "Sudden Spike"
                        ml_model = "Isolation Forest"
                    elif drift_chance < 0.50:
                        drift_type = "Gradual Change"
                        ml_model = "Z-Score"
                    elif drift_chance < 0.75:
                        drift_type = "Device Silence"
                        ml_model = "Autoencoder"
                    else:
                        drift_type = "Multiple Devices Changing"
                        ml_model = "KL Divergence"
                
                if row["status"] == "emergency":
                    reasons.insert(0, "ACTIVE EMERGENCY")
                    
                # Calculate Base Trust
                base_trust = max(100 - risk_score, 0)
                
                # Context-Aware Intelligence: Final Trust = Behavior Risk x Clinical Criticality x Deployment Exposure
                # To map it back to a 100 scale logically for the UI, we adjust the penalty portion.
                # penalty = risk_score * criticality * exposure
                crit = location_context[row["location"]]["criticality"]
                exp = location_context[row["location"]]["exposure"]
                
                adjusted_penalty = risk_score * crit * exp
                final_trust = max(100 - adjusted_penalty, 0)
                
                if final_trust < 100 and not reasons:
                    reasons.append("Minor telemetry fluctuations")
                    
                return pd.Series([
                    int(final_trust), 
                    reasons, 
                    drift_type, 
                    ml_model, 
                    round(crit, 1), 
                    round(exp, 1)
                ])
                
            df[["trust_score", "risk_reasons", "drift_type", "ml_model", "criticality", "exposure"]] = df.apply(calculate_trust_and_reasons, axis=1)
            
            def device_status(score):
                # Using specific LifeShield-X brackets
                if score >= 90: return "Safe"
                elif score >= 60: return "Warning"
                else: return "Compromised"
                
            df["device_health"] = df["trust_score"].apply(device_status)
            
            # Replace old boolean with new string label
            df["drift_detected"] = df["drift_type"]

            
            location_coords = {
                "Mall": [12.9716, 77.5946],             # UB City / MG Road
                "Airport": [13.1986, 77.7066],          # KIAL Airport
                "School": [12.9352, 77.6245],           # Koramangala
                "Metro Station": [12.9784, 77.6408],    # Indiranagar Metro
                "Corporate Park": [12.9259, 77.6229],   # Electronic City / Tech Park
                "Stadium": [12.9830, 77.5973],          # Chinnaswamy Stadium
                "ICU Hospital": [12.9340, 77.6100]      # NIMHANS / Apollo
            }
            
            # No jitter - place them exactly on the real locations
            df["lat"] = df["location"].map(lambda x: location_coords.get(x, [12.9716, 77.5946])[0])
            df["lon"] = df["location"].map(lambda x: location_coords.get(x, [12.9716, 77.5946])[1])

            records = df.to_dict(orient="records")
            
            # Create a clean list of dicts with primitive types only to avoid circular reference
            clean_records = []
            for r in records:
                clean_r = {}
                for k, v in r.items():
                    if isinstance(v, (np.integer, int)):
                        clean_r[k] = int(v)
                    elif isinstance(v, (np.floating, float)):
                        clean_r[k] = float(v)
                    elif isinstance(v, np.ndarray):
                        clean_r[k] = v.tolist()
                    elif isinstance(v, (np.bool_, bool)):
                        clean_r[k] = bool(v)
                    elif isinstance(v, list):
                        clean_r[k] = [str(x) for x in v] # convert lists (like risk_reasons) to list of strings
                    else:
                        clean_r[k] = str(v)
                clean_records.append(clean_r)
                
            json_data = json.dumps(clean_records)
            self.wfile.write(json_data.encode('utf-8'))
        else:
            return super().do_GET()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), AEDRequestHandler) as httpd:
        print(f"Server started. Access your app at: http://localhost:{PORT}/native_app.html")
        httpd.serve_forever()
