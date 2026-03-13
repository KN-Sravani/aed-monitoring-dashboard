import json
import random
import time

devices = [
    {"device": "AED-101", "latitude": 13.0827, "longitude": 80.2707},
    {"device": "AED-102", "latitude": 13.0850, "longitude": 80.2800},
    {"device": "AED-103", "latitude": 13.0800, "longitude": 80.2750},
    {"device": "AED-104", "latitude": 13.0700, "longitude": 80.2650}
]

# LifeShield-X Real-time Mock Simulator
risks = [
    "Policy Violation (Fake TLS / Unauthorized Cloud)",
    "Cyber Threat: Malware/Ransomware Signature",
    "Operational Problem: Corrupted Firmware",
    "Telemetry Anomaly: Hardware Silence Detected",
    "Data Exfiltration (Botnet Activity)"
]

while True:

    results = []

    for d in devices:

        trust_score = random.randint(40,100)

        risk_list = []

        if trust_score < 80:
            risk_list.append(random.choice(risks))

        results.append({
            "device": d["device"],
            "trust_score": trust_score,
            "latitude": d["latitude"],
            "longitude": d["longitude"],
            "last_used": "2026-03-10",
            "risk": risk_list
        })

    with open("../frontend/results.json","w") as f:
        json.dump(results,f,indent=4)

    print("Generated new device data")

    time.sleep(5)
