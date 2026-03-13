import csv
import json

results = []

with open("aed_logs.csv") as file:
    reader = csv.DictReader(file)

    for row in reader:

        device = row["device_id"]
        data = int(row["data_sent_MB"])
        server = row["server"]
        time = int(row["time"])
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        last_used = row["last_used"]

        # LifeShield-X Trust Calculator
        # Initial score
        risk_score = 0
        risks = []

        # 1. Policy Violation (Weight: 30%)
        if server != "hospital_server":
            risk_score += 30
            risks.append("Policy Violation (Unauthorized Cloud/Server)")

        # 2. Anomaly Score (Weight: 25%)
        if data > 50:
            risk_score += 25
            risks.append(f"Network Anomaly: High Data Transfer ({data} MB)")

        # 3. Behavior Drift (Weight: 15%)
        if time < 6 or time > 22:
            risk_score += 15
            risks.append(f"Behavior Drift: Abnormal Activity Time (Hour {time})")

        # Context-Aware Intelligence (Simplified mock criticality based on region)
        # Final Trust = 100 - (Risk * Criticality * Exposure)
        criticality = 1.2 if lat > 40.71 else 1.0
        exposure = 1.1 if lon > -74.00 else 1.0
        
        adjusted_penalty = risk_score * criticality * exposure
        final_trust = max(100 - adjusted_penalty, 0)

        results.append({
            "device": device,
            "trust_score": round(final_trust, 1),
            "risk": risks,
            "latitude": lat,
            "longitude": lon,
            "last_used": last_used,
            "criticality": criticality,
            "exposure": exposure
        })

with open("results.json", "w") as outfile:
    json.dump(results, outfile, indent=4)

print("Analysis complete. Results generated with location data.")
