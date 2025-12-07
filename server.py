import os
import json
import threading
import requests
from flask import Flask, redirect, request
from urllib.parse import urlencode

# --- credentials.json を最初に作る ---
creds_env = os.environ.get("GCP_CREDENTIALS_JSON")
if creds_env:
    with open("credentials.json", "w", encoding="utf-8") as f:
        f.write(creds_env)
    print("credentials.json generated!")
else:
    print("GCP_CREDENTIALS_JSON not found")


# --- Flask app ---
app = Flask(__name__)

# --- Home ページ ---
@app.route("/")
def home():
    return """
    <h1>Discord Bot: カレンダー通知アプリ</h1>
    <p>このアプリは Google Calendar の予定を読み取り、Discord に通知するサービスです。</p>
    <p>プライバシーポリシーは <a href="/privacy">こちら</a></p>
    <p>Google 認証は <a href="/auth">こちら</a></p>
    """


# --- プライバシーポリシー ---
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
        <p>このアプリ（Discord Bot）は、ユーザーの Google Calendar 予定を読み取り、
        Discord 上でリマインド通知を提供するためにのみ使用します。</p>

        <h2>収集する情報</h2>
        <p>- Google Calendar イベント（読み取り専用）<br>
        - Discord ID（通知送信のため）</p>

        <h2>利用目的</h2>
        <p>- Google Calendar の予定を Discord に通知するためのみ使用します。</p>

        <h2>共有について</h2>
        <p>- いかなる第三者にも情報を提供しません。</p>

        <h2>お問い合わせ</h2>
        <p>- doragonnfurai5026@gmail.com</p>
    </body>
    </html>
    """


# --- Google OAuth 認証開始 ---
@app.route("/auth")
def auth():
    with open("credentials.json", "r", encoding="utf-8") as f:
        creds = json.load(f)

    client_id = creds["web"]["client_id"]
    redirect_uri = creds["web"]["redirect_uris"][0]

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


# --- Google OAuth callback ---
@app.route("/callback")
def callback():
    code = request.args.get("code")

    with open("credentials.json", "r", encoding="utf-8") as f:
        creds = json.load(f)

    client_id = creds["web"]["client_id"]
    client_secret = creds["web"]["client_secret"]
    redirect_uri = creds["web"]["redirect_uris"][0]
    token_uri = creds["web"]["token_uri"]

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    token_res = requests.post(token_uri, data=data)
    print("TOKEN RESPONSE:", token_res.json())

    return "Google OAuth Success! You can close this page."


# --- Discord Bot 部分 ---
import discord

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content == "!ping":
        await message.channel.send("pong!")


def run_discord_bot():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token is None:
        print("DISCORD_BOT_TOKEN is not set!")
    bot.run(token)


# --- Flask と Discord Bot を同時起動 ---
if __name__ == "__main__":
    threading.Thread(target=run_discord_bot, daemon=True).start()
    app.run(port=5000)
