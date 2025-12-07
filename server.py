from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot server is running!"

if __name__ == "__main__":
    app.run(port=5000)

import os

# Render の環境変数から credentials.json を作成
if "GCP_CREDENTIALS_JSON" in os.environ:
    with open("credentials.json", "w", encoding="utf-8") as f:
        f.write(os.environ["GCP_CREDENTIALS_JSON"])

