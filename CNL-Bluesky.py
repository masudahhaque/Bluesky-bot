import json
import os
import gspread
from google.oauth2.service_account import Credentials
from atproto import Client

# Define the scope
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authenticate Google Sheets with credentials
creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
gc = gspread.authorize(creds)

# Open the Google Sheet
sheet = gc.open('Crisis Sheet').sheet1

# Load Bluesky credentials from a JSON file
with open("secrets/credentials.json", "r") as f: 
    creds = json.load(f)

username = creds["BLUESKY_USERNAME"]
password = creds["BLUESKY_PASSWORD"]

# Authorize Bluesky connection
client = Client()
client.login(username, password)

STATE_FILE = "truck_state.json"
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        last_state = json.load(f)

else:
    last_state = {}

data = sheet.get_all_records()
current_state = {}
posts_to_make = []

for row in data:
    truck = str(row.get("Truck ID", "")).strip()
    alert_msg = str(row.get("Alert Message", "")).strip().lower()
    resolved = str(row.get("Resolved", "")).strip().lower()
    lat = str(row.get("Latitude", "")).strip()
    lon = str(row.get("Longitude", "")).strip()
    radiation = str(row.get("Radiation Level (µSv/h)", "")).strip()

    if not truck:
        continue

    status = "resolved" if resolved in ["yes", "true", "resolved"] else "unresolved"
    current_state[truck] = status
    prev_status = last_state.get(truck, "")

    # --- Case 1: New high radiation alert ---
    if "high radiation" in alert_msg and status == "unresolved":
        if prev_status != "unresolved":
            msg_en = f"🚨 Alert: Truck {truck} detected high radiation ({radiation} µSv/h) near ({lat}, {lon})."
            msg_fr = f"🚨 Alerte : Le camion {truck} a détecté un niveau de radiation élevé ({radiation} µSv/h) près de ({lat}, {lon})."
            posts_to_make.append(f"{msg_en}\n{msg_fr}")

    # --- Case 2: Resolved alert ---
    elif status == "resolved" and prev_status == "unresolved":
        msg_en = f"✅ Update: The radiation issue for Truck {truck} has been resolved."
        msg_fr = f"✅ Mise à jour : Le problème de radiation pour le camion {truck} a été résolu."
        posts_to_make.append(f"{msg_en}\n{msg_fr}")

# === POST TO BLUESKY ===
if posts_to_make:
    for post_text in posts_to_make:
        client.send_post(post_text)
        print("Posted to Bluesky:", post_text)
else:
    print("No new alerts or updates to post.")

# === SAVE STATE ===
with open(STATE_FILE, "w") as f:
    json.dump(current_state, f, indent=2)
