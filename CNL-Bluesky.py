import json
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

post = client.send_post('This is an alert.')