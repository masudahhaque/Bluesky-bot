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

# Load previous state with error handling
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if content:
                last_state = json.loads(content)
            else:
                last_state = {}
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Could not load state file: {e}. Starting fresh.")
        last_state = {}
else:
    print("No previous state found. Starting fresh.")
    last_state = {}

data = sheet.get_all_records()
for row in data:
    truck_id = row["Truck ID"]
    alert_message = row["Alert Message"]
    resolved = row["Resolved"]  # This should be a Boolean (True/False)
    latitude = row["Latitude"]
    longitude = row["Longitude"]

    # Create unique ID per truck
    key = str(truck_id)

    # CASE 1: New alert (not yet posted)
    if alert_message and "high radiation" in alert_message.lower() and not resolved and last_state.get(key) != "alerted":
        message_en = f"🚨 ALERT: Truck #{truck_id} at ({latitude}, {longitude}) is experiencing high radiation levels."
        message_fr = f"🚨 ALERTE : Le camion #{truck_id} à ({latitude}, {longitude}) présente un niveau élevé de radiation."
        client.send_post(message_en)
        client.send_post(message_fr)
        last_state[key] = "alerted"
        print("Posted alert:", message_en)

    # CASE 2: Issue resolved (True)
    elif resolved and last_state.get(key) == "alerted":
        message_en = f"✅ UPDATE: Truck #{truck_id} has resolved its high radiation issue."
        message_fr = f"✅ MISE À JOUR : Le camion #{truck_id} a résolu son problème de radiation élevée."
        client.send_post(message_en)
        client.send_post(message_fr)
        last_state[key] = "resolved"
        print("Posted resolution:", message_en)

# -------------------- SAVE UPDATED STATES --------------------
with open("truck_state.json", "w") as f:
    json.dump(last_state, f, indent=4)
