import csv
import random
from datetime import datetime, timedelta

# Expanded device list (15 devices)
devices = [f"AED{str(i).zfill(2)}" for i in range(1, 16)]
servers = ["hospital_server","hospital_server","hospital_server","unknown_server"]

# Central coordinates (e.g., a hypothetical hospital campus)
base_lat = 40.7128
base_lon = -74.0060

rows = []

for i in range(150):
    device = random.choice(devices)
    data = random.randint(1,150)
    server = random.choice(servers)
    time_hour = random.randint(0,23)
    
    # Generate a random location near the base
    lat = base_lat + random.uniform(-0.015, 0.015)
    lon = base_lon + random.uniform(-0.015, 0.015)
    
    # Generate a random "last used" timestamp within the last 30 days
    days_ago = random.randint(0, 30)
    hours_ago = random.randint(0, 23)
    mins_ago = random.randint(0, 59)
    last_used = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)
    last_used_str = last_used.isoformat()

    rows.append([device, data, server, time_hour, lat, lon, last_used_str])

with open("aed_logs.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["device_id", "data_sent_MB", "server", "time", "latitude", "longitude", "last_used"])
    writer.writerows(rows)

print("Generated 150 IoT log records with location and timestamp data.")
