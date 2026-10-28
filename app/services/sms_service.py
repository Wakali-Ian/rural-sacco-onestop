"""SMS via Africa's Talking. Falls back to console logging when AT_API_KEY is missing."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def send_sms(phone, message, dev_mode=None):
    if dev_mode is None:
        dev_mode = not os.getenv("AT_API_KEY")

    if dev_mode:
        print(f"[SMS-DEV] To {phone}: {message}")
        return {"status": "dev_logged", "to": phone}

    username = os.getenv("AT_USERNAME", "sandbox")
    api_key = os.getenv("AT_API_KEY", "")
    sender = os.getenv("AT_SENDER_ID", "")
    url = ("https://api.africastalking.com/version1/messaging"
           if username != "sandbox"
           else "https://api.sandbox.africastalking.com/version1/messaging")
    headers = {"apiKey": api_key, "Accept": "application/json"}
    data = {"username": username, "to": phone, "message": message}
    if sender:
        data["from"] = sender
    r = requests.post(url, headers=headers, data=data, timeout=15)
    r.raise_for_status()
    return r.json()
