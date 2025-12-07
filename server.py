import os
import json
from flask import Flask

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

if __name__ == "__main__":
    app.run(port=5000)
