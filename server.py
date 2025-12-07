import os
import json
from flask import Flask, redirect
from urllib.parse import urlencode

# --- credentials.json を最初に作る ---
creds = os.environ.get("GCP_CREDENTIALS_JSON")
if creds:
    with open("credentials.json", "w", encoding="utf-8") as f:
        f.write(creds)
    print("credentials.json generated!")
else:
    print("GCP_CREDENTIALS_JSON not found")

# --- Flask app ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot server is running!"

# --- Google OAuth /auth エンドポイント ---
@app.route("/auth")
def auth():
    # credentials.json を読み込む
    with open("credentials.json", "r", encoding="utf-8") as f:
        creds = json.load(f)

    client_id = creds["web"]["client_id"]
    redirect_uri = creds["web"]["redirect_uris"][0]

    # Google OAuth のURLを作成
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.readonly",
        "access_type": "offline",
        "prompt": "consent"
    }

    auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)

    return redirect(auth_url)

# --- 最後にだけ置く ---
if __name__ == "__main__":
    app.run(port=5000)
