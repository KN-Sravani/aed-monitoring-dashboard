import pandas as pd
from sklearn.ensemble import IsolationForest

# LifeShield-X: Drift Classification & Anomaly Detection Engine

# Load dataset
data = pd.read_csv("aed_logs.csv")

# Feature Extractor -> We analyze telemetry like data sent and time of day
features = data[["data_sent_MB", "time"]]

# ML Model: Isolation Forest (Used to detect Sudden Spikes and Unknown Attacks)
model = IsolationForest(contamination=0.1, random_state=42)

# Predict anomalies (-1 for anomaly, 1 for normal)
data["anomaly_score"] = model.fit_predict(features)

# Map numeric output to LifeShield-X labels
data["drift_type"] = data["anomaly_score"].apply(
    lambda x: "Sudden Spike (Isolation Forest)" if x == -1 else "Normal"
)

# Display specific anomalous rows indicating a potential Cyber Threat
anomalies = data[data["anomaly_score"] == -1]
print(f"Lifeshield-X Engine Detected {len(anomalies)} anomalies in telemetry:")
print(anomalies[["device_id", "data_sent_MB", "server", "time", "drift_type"]])