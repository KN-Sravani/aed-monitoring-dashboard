import streamlit as st
import mysql.connector
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_geolocation import streamlit_geolocation

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="LifeShield-X Security Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
"""
<h1 style='text-align:center; color:red;'>🛡️ LifeShield-X</h1>
<p style='text-align:center;'>Intelligent AED Security & Monitoring</p>
""",
unsafe_allow_html=True
)

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Nsravani@123",
    database="aed_system"
)

query = "SELECT * FROM aed_data ORDER BY timestamp DESC"
df = pd.read_sql(query, db)

# -----------------------------
# SIMULATED NETWORK METRICS
# -----------------------------
df["suspicious_message_rate"] = np.random.randint(0,100,len(df))
df["packet_delay"] = np.random.randint(50,5000,len(df))
df["unauthorized_access"] = np.random.choice([True,False],len(df))

# -----------------------------
# TRUST SCORE CALCULATION
# -----------------------------
def calculate_trust(row):

    # Base Trust Score
    risk = 0

    if row["status"] == "emergency":
        risk += 40

    if row["battery_level"] < 30:
        risk += 30

    if row["heart_rate_detected"] > 120 or row["heart_rate_detected"] < 50:
        risk += 20

    if row["suspicious_message_rate"] > 50:
        risk += 15

    if row["packet_delay"] > 3000:
        risk += 10

    if row["unauthorized_access"]:
        risk += 25

    # Context-Aware Intelligence (Criticality & Exposure)
    # Hospital/ICU (High Criticality), Airport (High Exposure)
    criticality = 1.5 if row["location"] in ["Hospital", "ICU", "Mall"] else 1.0
    exposure = 1.2 if row["location"] in ["Airport", "Metro Station", "Mall"] else 1.0
    
    adjusted_risk = risk * criticality * exposure
    return max(100 - adjusted_risk, 0)

df["trust_score"] = df.apply(calculate_trust,axis=1)

# -----------------------------
# DEVICE HEALTH STATUS
# -----------------------------
def device_status(score):

    if score >= 90:
        return "🟢 Safe (90-100)"
    elif score >= 60:
        return "🟡 Warning (60-89)"
    else:
        return "🔴 Compromised"

df["device_health"] = df["trust_score"].apply(device_status)

# -----------------------------
# DRIFT DETECTION
# -----------------------------
# Determine Drift Profile & ML model
def extract_drift(row):
    if row["heart_rate_detected"] > 120 or row["heart_rate_detected"] < 50:
        return "Sudden Spike"
    elif row["battery_level"] < 20:
        return "Gradual Change"
    elif row["packet_delay"] > 3000:
        return "Device Silence"
    return "Normal"

def extract_ml_model(row):
    drift = extract_drift(row)
    if drift == "Sudden Spike": return "Isolation Forest"
    if drift == "Gradual Change": return "Autoencoder"
    if drift == "Device Silence": return "Z-Score"
    return "None"

df["drift_type"] = df.apply(extract_drift, axis=1)
df["ml_engine"] = df.apply(extract_ml_model, axis=1)

# -----------------------------
# AED LOCATIONS
# -----------------------------
location_coords = {
    "Mall":[12.9716,77.5946],
    "Airport":[13.1986,77.7066],
    "School":[12.9352,77.6245],
    "Metro Station":[12.9784,77.6408]
}

df["lat"] = df["location"].map(lambda x: location_coords[x][0])
df["lon"] = df["location"].map(lambda x: location_coords[x][1])

# -----------------------------
# DISTANCE CALCULATION
# -----------------------------
import math

def distance(lat1, lon1, lat2, lon2):

    R = 6371  # Earth radius in KM

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon/2)**2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c
# -----------------------------
# SIDEBAR MENU
# -----------------------------
menu = st.sidebar.selectbox(
    "Navigation",
    [
        "Home",
        "Find Nearest AED",
        "AED Map",
        "Device Monitoring",
        "Trust Score Analytics",
        "Emergency Instructions"
    ]
)

# -----------------------------
# HOME PAGE
# -----------------------------
if menu == "Home":

    st.header("🌍 City Emergency Dashboard")

    total_devices = len(df)
    low_battery = len(df[df["battery_level"] < 30])
    emergencies = len(df[df["status"] == "emergency"])

    network_risk = len(df[
        (df["suspicious_message_rate"] > 50) |
        (df["packet_delay"] > 3000) |
        (df["unauthorized_access"] == True)
    ])

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🚑 Total AED Devices", total_devices)
    col2.metric("🔋 Low Battery Devices", low_battery)
    col3.metric("🚨 Emergency Alerts", emergencies)
    col4.metric("🌐 Network Risks", network_risk)

    st.subheader("📊 Live AED Device Data")

    st.dataframe(df)

    st.subheader("🚨 Emergency Devices")

    emergency_devices = df[df["status"] == "emergency"]

    if not emergency_devices.empty:

        st.error("Cardiac emergency detected in these devices")

        st.dataframe(emergency_devices[
            ["device_id","location","battery_level","heart_rate_detected"]
        ])

    else:

        st.success("No emergency alerts currently")

    st.subheader("⚠ Risky Devices")

    risky_devices = df[df["trust_score"] < 60]

    if not risky_devices.empty:

        st.warning("Some devices show risky behavior")

        st.dataframe(risky_devices[
            ["device_id","location","trust_score","device_health"]
        ])

    else:

        st.success("All devices operating safely")

# -----------------------------
# NEAREST AED
# -----------------------------
elif menu == "Find Nearest AED":

    st.subheader("🚑 Find Nearest Safe AED Device")

    location = streamlit_geolocation()

    if location["latitude"] is not None:

        user_lat = location["latitude"]
        user_lon = location["longitude"]

        st.success("📍 Your Location Detected")

        st.write("Latitude:", user_lat)
        st.write("Longitude:", user_lon)

        # Calculate distance to each AED
        df["distance"] = df.apply(
            lambda row: distance(row["lat"], row["lon"], user_lat, user_lon),
            axis=1
        )

        # Find nearest AED
        nearest = df.loc[df["distance"].idxmin()]

        st.subheader("Nearest AED Device")

        st.write("Device ID:", nearest["device_id"])
        st.write("Location:", nearest["location"])
        st.write("Battery Level:", nearest["battery_level"], "%")
        st.write("Trust Score:", nearest["trust_score"])
        st.write("Distance:", round(nearest["distance"],2), "KM")

        # Check trust score
        if nearest["trust_score"] < 60:

            st.warning("⚠ Nearest AED has low trust score")

            safe_devices = df[df["trust_score"] >= 60]

            if not safe_devices.empty:

                safe_devices["distance"] = safe_devices.apply(
                    lambda row: distance(row["lat"], row["lon"], user_lat, user_lon),
                    axis=1
                )

                alternative = safe_devices.loc[safe_devices["distance"].idxmin()]

                st.success("Recommended Alternative AED")

                st.write("Device ID:", alternative["device_id"])
                st.write("Location:", alternative["location"])
                st.write("Battery Level:", alternative["battery_level"], "%")
                st.write("Trust Score:", alternative["trust_score"])
                st.write("Distance:", round(alternative["distance"],2), "KM")

            else:

                st.error("No safe AED devices available nearby")

        else:

            st.success("Nearest AED is safe to use")

    else:

        st.warning("⚠ Please allow location access in your browser")

# -----------------------------
# MAP PAGE
# -----------------------------
elif menu == "AED Map":

    st.subheader("📍 AED Device Locations")

    st.map(df[["lat","lon"]])

# -----------------------------
# DEVICE MONITORING
# -----------------------------
elif menu == "Device Monitoring":

    st.subheader("📊 Device Monitoring Dashboard")

    st.dataframe(df[
        [
            "device_id",
            "location",
            "battery_level",
            "heart_rate_detected",
            "trust_score",
            "device_health",
            "drift_type",
            "ml_engine"
        ]
    ])

    st.subheader("🔋 Battery Warnings")

    low_battery = df[df["battery_level"]<30]

    if not low_battery.empty:

        st.warning("Some AED devices have low battery")

        st.dataframe(
            low_battery[
                ["device_id","location","battery_level"]
            ]
        )

    else:

        st.success("All AED batteries are healthy")

# -----------------------------
# TRUST SCORE ANALYTICS
# -----------------------------
elif menu == "Trust Score Analytics":

    st.subheader("🔐 IoT Trust Score Analytics")

    st.dataframe(df[
        [
            "device_id",
            "location",
            "trust_score",
            "device_health",
            "drift_type",
            "ml_engine"
        ]
    ])

    fig = px.bar(
        df,
        x="device_id",
        y="trust_score",
        color="trust_score",
        color_continuous_scale="RdYlGn",
        title="Trust Score of AED Devices"
    )

    st.plotly_chart(fig)

    st.subheader("🌐 Network Anomalies")

    network_risky = df[
        (df["suspicious_message_rate"]>50) |
        (df["packet_delay"]>3000) |
        (df["unauthorized_access"]==True)
    ]

    if not network_risky.empty:

        st.warning("Suspicious network behavior detected")

        st.dataframe(network_risky[
            [
                "device_id",
                "location",
                "suspicious_message_rate",
                "packet_delay",
                "unauthorized_access"
            ]
        ])

    else:

        st.success("All devices network behavior normal")

# -----------------------------
# EMERGENCY INSTRUCTIONS
# -----------------------------
elif menu == "Emergency Instructions":

    st.subheader("❤️ Cardiac Emergency Steps")

    st.write("1️⃣ Call emergency services immediately")
    st.write("2️⃣ Bring the nearest AED device")
    st.write("3️⃣ Attach AED pads to the patient")
    st.write("4️⃣ Follow AED voice instructions")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")

st.markdown(
"LifeShield-X | Intelligent AED Security & Monitoring"
)
