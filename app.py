import discord
import datetime
import requests
import pytz
from dotenv import load_dotenv
import os
from flask import Flask
from threading import Thread

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CLIST_USERNAME = os.getenv("CLIST_USERNAME")
CLIST_API_KEY = os.getenv("CLIST_API_KEY")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

preferred_platforms = [
    'leetcode.com',
    'codeforces.com',
    'codechef.com',
    'naukri.com/code360',
    'atcoder.jp',
    'hackerrank.com',
    'hackerearth.com'
]

def get_all_contests():
    now = datetime.datetime.utcnow()
    end = now + datetime.timedelta(days=7)

    url = "https://clist.by/api/v4/contest/"
    params = {
        'username': CLIST_USERNAME,
        'api_key': CLIST_API_KEY,
        'start__gte': now.isoformat(),
        'start__lt': end.isoformat(),
        'order_by': 'start'
    }

    response = requests.get(url, params=params)
    data = response.json()
    return data.get('objects', [])

def get_global_message(contests):
    ist = pytz.timezone('Asia/Kolkata')
    msg = "**🌍 Upcoming Global Coding Contests (Next 7 Days):**\n"
    for c in contests:
        start_str = c.get('start')
        try:
            start_utc = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            start_ist = start_utc.astimezone(ist)
            formatted_start = start_ist.strftime("%d %b %Y, %A %I:%M %p IST")
        except Exception:
            formatted_start = start_str or "Unknown start time"

        event = c.get('event', 'Unnamed Contest')
        resource = c.get('resource', 'Unknown Platform')
        href = c.get('href', '')

        msg += f"\n• **{event}** on `{resource}`\n   ⏰ {formatted_start}\n   🔗 <{href}>\n"
    return msg

def get_preferred_message(contests):
    msg = "**🎯 Your Preferred Contests (Next 7 Days):**\n"
    for c in contests:
        resource = c.get('resource', '')
        if resource not in preferred_platforms:
            continue

        event = c.get('event', 'Unnamed Contest')
        href = c.get('href', '')
        start = c.get('start', 'Unknown time')

        msg += f"\n• **{event}** on `{resource}`\n   ⏰ {start}\n   🔗 <{href}>\n"
    return msg

async def send_long_message(channel, message):
    parts = [message[i:i+1900] for i in range(0, len(message), 1900)]
    for part in parts:
        await channel.send(part)

async def send_contest_updates():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"❌ Channel with ID {CHANNEL_ID} not found!")
        return

    contests = get_all_contests()
    global_msg = get_global_message(contests)
    preferred_msg = get_preferred_message(contests)

    await send_long_message(channel, global_msg)
    await send_long_message(channel, preferred_msg)

    print("✅ Contest messages sent!")

@client.event
async def on_ready():
    print(f"✅ {client.user} is online!")
    # Don't send messages on startup automatically

# Flask app for uptime monitoring and trigger
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

@app.route('/send')
def send():
    # Schedule the async task in the event loop
    client.loop.create_task(send_contest_updates())
    return "Contest messages triggered!", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Run Flask server in a background thread
Thread(target=run_flask).start()

# Run the Discord bot
client.run(TOKEN)
