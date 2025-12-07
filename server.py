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


# ---------------------------------------------------------
#  Google OAuth の token.json を保存するフォルダ
# ---------------------------------------------------------
TOKEN_FILE = "token.json"


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

    token_res = requests.post(token_uri, data=data).json()

    # --- token.json 保存 ---
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(token_res, f, indent=2)

    print("TOKEN RESPONSE SAVED!")
    return "Google OAuth Success! You can close this page."


# ---------------------------------------------------------
# Google Calendar 予定取得
# ---------------------------------------------------------
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime


def get_calendar_events(days_from_now: int):
    """今日・明日の予定を取得"""

    # 認証トークン読み込み
    if not os.path.exists(TOKEN_FILE):
        return None, None

    creds = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        ["https://www.googleapis.com/auth/calendar.readonly"]
    )

    service = build("calendar", "v3", credentials=creds)

    target_date = datetime.date.today() + datetime.timedelta(days=days_from_now)
    start = datetime.datetime.combine(target_date, datetime.time.min).isoformat() + "Z"
    end = datetime.datetime.combine(target_date, datetime.time.max).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])
    return target_date, events


# ---------------------------------------------------------
# Discord Bot
# ---------------------------------------------------------
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")


@bot.command()
async def ping(ctx):
    await ctx.send("pong!")


@bot.command()
async def today(ctx):
    date, events = get_calendar_events(0)
    if date is None:
        await ctx.send("Google 認証がまだです。/auth を開いて認証してください。")
        return

    if not events:
        await ctx.send(f"{date} の予定はありません！")
        return

    msg = f"**📅 {date} の予定**\n\n"
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        msg += f"・{start} : {e.get('summary', '無題')}\n"

    await ctx.send(msg)


@bot.command()
async def tomorrow(ctx):
    date, events = get_calendar_events(1)
    if date is None:
        await ctx.send("Google 認証がまだです。/auth を開いて認証してください。")
        return

    if not events:
        await ctx.send(f"{date} の予定はありません！")
        return

    msg = f"**📅 {date} の予定**\n\n"
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date"))
        msg += f"・{start} : {e.get('summary', '無題')}\n"

    await ctx.send(msg)


# --- Discord Bot 起動 ---
def run_discord_bot():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token is None:
        print("DISCORD_BOT_TOKEN is not set!")
    bot.run(token)


threading.Thread(target=run_discord_bot, daemon=True).start()


# --- Flask を gunicorn 用に公開 ---
# (ここはそのままで OK)
