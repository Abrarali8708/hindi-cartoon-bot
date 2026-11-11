"""Run ONCE on your own PC to connect the bot to your YouTube channel.

1. Put the client_secret.json you downloaded from Google Cloud next to this file.
2. Run:  python get_refresh_token.py
3. A browser opens -> choose your channel's Google account -> Allow.
4. Copy the 3 values it prints into GitHub Secrets.
"""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json", ["https://www.googleapis.com/auth/youtube.upload"])
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
info = json.load(open("client_secret.json"))
info = info.get("installed") or info.get("web")
print("\nAdd these as GitHub Secrets:\n")
print("YT_CLIENT_ID      =", info["client_id"])
print("YT_CLIENT_SECRET  =", info["client_secret"])
print("YT_REFRESH_TOKEN  =", creds.refresh_token)
