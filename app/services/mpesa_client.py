"""Minimal Safaricom Daraja client. Works in sandbox with real keys.

If MPESA_CONSUMER_KEY/SECRET are missing, calling methods raises a clear
RuntimeError instead of failing silently.
"""
import base64
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class DarajaClient:
    def __init__(self):
        self.env = os.getenv("MPESA_ENV", "sandbox")
        self.key = os.getenv("MPESA_CONSUMER_KEY", "")
        self.secret = os.getenv("MPESA_CONSUMER_SECRET", "")
        self.shortcode = os.getenv("MPESA_SHORTCODE", "174379")
        self.passkey = os.getenv("MPESA_PASSKEY", "")
        self.callback = os.getenv("MPESA_CALLBACK_URL", "")
        self.base = ("https://api.safaricom.co.ke" if self.env == "production"
                     else "https://sandbox.safaricom.co.ke")

    def _auth(self):
        if not self.key or not self.secret:
            raise RuntimeError("MPESA_CONSUMER_KEY/SECRET missing in .env")
        creds = base64.b64encode(f"{self.key}:{self.secret}".encode()).decode()
        r = requests.get(
            f"{self.base}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {creds}"}, timeout=15,
        )
        r.raise_for_status()
        return r.json()["access_token"]

    def stk_push(self, phone, amount, account_ref, description="Payment"):
        token = self._auth()
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        pw = base64.b64encode(
            f"{self.shortcode}{self.passkey}{ts}".encode()).decode()
        p = "".join(c for c in phone if c.isdigit())
        if p.startswith("0"):
            p = "254" + p[1:]
        elif p.startswith(("7", "1")):
            p = "254" + p
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": pw,
            "Timestamp": ts,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": p, "PartyB": self.shortcode, "PhoneNumber": p,
            "CallBackURL": self.callback,
            "AccountReference": account_ref,
            "TransactionDesc": description,
        }
        r = requests.post(
            f"{self.base}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}, timeout=30,
        )
        r.raise_for_status()
        return r.json()
