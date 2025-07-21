import json
import os
from datetime import datetime

USER_FILE = "user_data.json"
REF_FILE = "referral_data.json"

def get_user_data():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_user_data(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_referral_data():
    if not os.path.exists(REF_FILE):
        return {}
    with open(REF_FILE, "r") as f:
        return json.load(f)

def save_referral_data(data):
    with open(REF_FILE, "w") as f:
        json.dump(data, f, indent=2)

def reset_daily_downloads():
    data = get_user_data()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for user_id in data:
        data[user_id]["downloads"] = 0
        data[user_id]["last_reset"] = today
    save_user_data(data)