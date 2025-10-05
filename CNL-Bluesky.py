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
print("🔐 Authenticating with Google Sheets...")
creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
gc = gspread.authorize(creds)

# Open the Google Sheet
print("📊 Opening Google Sheet...")
sheet = gc.open('Crisis Sheet').sheet1

# Load Bluesky credentials from a JSON file
print("🔐 Loading Bluesky credentials...")
with open("secrets/credentials.json", "r") as f: 
    creds = json.load(f)

username = creds["BLUESKY_USERNAME"]
password = creds["BLUESKY_PASSWORD"]

# Authorize Bluesky connection
print("🦋 Logging into Bluesky...")
client = Client()
client.login(username, password)
print("✅ Bluesky login successful!")

STATE_FILE = "truck_state.json"

# Load previous state with error handling
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if content:
                last_state = json.loads(content)
                print(f"📂 Loaded previous state: {last_state}")
            else:
                last_state = {}
                print("📂 State file was empty, starting fresh")
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Warning: Could not load state file: {e}. Starting fresh.")
        last_state = {}
else:
    print("📂 No previous state found. Starting fresh.")
    last_state = {}

print("\n📥 Fetching data from Google Sheet...")
data = sheet.get_all_records()
print(f"📊 Found {len(data)} rows in sheet\n")

posts_made = 0

for i, row in enumerate(data):
    print(f"--- Row {i+1} ---")
    truck_id = row.get("Truck ID", "")
    alert_message = row.get("Alert Message", "")
    resolved = row.get("Resolved", "")
    latitude = row.get("Latitude", "")
    longitude = row.get("Longitude", "")
    
    print(f"  Truck ID: {truck_id}")
    print(f"  Alert Message: '{alert_message}'")
    print(f"  Resolved: '{resolved}' (type: {type(resolved)})")
    print(f"  Location: ({latitude}, {longitude})")
    
    # Create unique ID per truck
    key = str(truck_id)
    previous_state = last_state.get(key, "none")
    print(f"  Previous State: {previous_state}")
    
    # Convert resolved to boolean
    resolved_bool = str(resolved).lower() in ['true', 'yes', '1', 'resolved']
    print(f"  Resolved (bool): {resolved_bool}")
    
    # Check if alert message contains "high radiation"
    has_high_rad = "high radiation" in str(alert_message).lower()
    print(f"  Has 'high radiation': {has_high_rad}")
    
    # CASE 1: New alert (not yet posted)
    if alert_message and has_high_rad and not resolved_bool and previous_state != "alerted":
        print(f"  ➡️ POSTING NEW ALERT for Truck {truck_id}")
        message_en = f"🚨 ALERT: Truck #{truck_id} at ({latitude}, {longitude}) is experiencing high radiation levels."
        message_fr = f"🚨 ALERTE : Le camion #{truck_id} à ({latitude}, {longitude}) présente un niveau élevé de radiation."
        try:
            client.send_post(message_en)
            client.send_post(message_fr)
            last_state[key] = "alerted"
            posts_made += 2
            print(f"  ✅ Posted alert: {message_en}")
        except Exception as e:
            print(f"  ❌ Error posting alert: {e}")
    
    # CASE 2: Issue resolved (True)
    elif resolved_bool and previous_state == "alerted":
        print(f"  ➡️ POSTING RESOLUTION for Truck {truck_id}")
        message_en = f"✅ UPDATE: Truck #{truck_id} has resolved its high radiation issue."
        message_fr = f"✅ MISE À JOUR : Le camion #{truck_id} a résolu son problème de radiation élevée."
        try:
            client.send_post(message_en)
            client.send_post(message_fr)
            last_state[key] = "resolved"
            posts_made += 2
            print(f"  ✅ Posted resolution: {message_en}")
        except Exception as e:
            print(f"  ❌ Error posting resolution: {e}")
    else:
        print(f"  ⏭️ No action needed")
    
    print()

# -------------------- SAVE UPDATED STATES --------------------
print(f"\n💾 Saving state: {last_state}")
with open("truck_state.json", "w") as f:
    json.dump(last_state, f, indent=4)

print(f"✅ Complete! Made {posts_made} posts total.")
print(f"\n📄 Final state file:")
with open(STATE_FILE, "r") as f:
    print(f.read())
