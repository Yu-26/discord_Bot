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

import requests
from flask import request

@app.route("/callback")
def callback():
    # Google から返ってきた code を取得
    code = request.args.get("code")

    # credentials.json 読み込み
    with open("credentials.json", "r", encoding="utf-8") as f:
        creds = json.load(f)

    client_id = creds["web"]["client_id"]
    client_secret = creds["web"]["client_secret"]
    redirect_uri = creds["web"]["redirect_uris"][0]
    token_uri = creds["web"]["token_uri"]

    # code → アクセストークン に変換
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    # Google のトークンエンドポイントへ POST
    token_res = requests.post(token_uri, data=data)
    token_json = token_res.json()

    # デバッグ表示用
    print("TOKEN RESPONSE:", token_json)

    return "Google OAuth Success! You can close this page."
@app.route("/privacy")
def privacy():
    return """
    <!DOCTYPE html>
    <html lang='ja'>
    <head>
        <meta charset='UTF-8'>
        <title>プライバシーポリシー</title>
    </head>
    <body>
        <h1>プライバシーポリシー</h1>
        <p>このアプリ（Discord Bot）は、ユーザーの Google Calendar 予定を読み取り、Discord 上でリマインド通知を提供するためにのみ使用します。</p>

        <h2>収集する情報</h2>
        <p>- ユーザーの Google Calendar の予定（読み取り専用）<br>
        - Discord ID（Bot が通知を送るため）</p>

        <h2>情報の利用目的</h2>
        <p>- カレンダーの予定を Discord に通知するため<br>
        - 他の目的で使用することはありません</p>

        <h2>情報の共有</h2>
        <p>- ユーザーの許可なしに第三者に情報を提供することはありません</p>

        <h2>セキュリティ</h2>
        <p>- 収集した情報は安全に保管されます<br>
        - 外部に公開されることはありません</p>

        <h2>お問い合わせ</h2>
        <p>- 問い合わせは doragonnfurai5026@gmail.com までご連絡ください</p>
    </body>
    </html>
    """
@app.route("/")
def home():
    return """
    <h1>Discord Bot: カレンダー通知アプリ</h1>
    <p>このアプリは Google Calendar の予定を読み取り、Discord に通知するサービスです。</p>
    <p>プライバシーポリシーは <a href="/privacy">こちら</a></p>
    """


# --- 最後にだけ置く ---
if __name__ == "__main__":
    app.run(port=5000)
