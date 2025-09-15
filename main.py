import os
import discord
from discord.ext import commands, tasks
import requests

# ===== إعدادات البوت =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")     # التوكن من Render → Environment
CHANNEL_ID = 1417061905423667301           # معرف القناة اللي يرسل فيها البوت

# ===== مفتاح الأخبار =====
API_KEY = os.getenv("NEWS_API_KEY")        # مفتاح الأخبار من Render → Environment

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== روابط اللوجو حسب نوع الخبر =====
LOGOS = {
    "higher": "https://link-to-green-logo.png",
    "lower": "https://link-to-red-logo.png",
    "expected": "https://link-to-blue-logo.png"
}

# ===== جلب الأخبار من NewsAPI =====
def get_news():
    if not API_KEY:
        print("⚠️ ما لقيت NEWS_API_KEY في Environment Variables")
        return None

    url = f"https://newsapi.org/v2/top-headlines?category=business&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "articles" in data and len(data["articles"]) > 0:
        article = data["articles"][0]
        return {
            "title": article["title"],
            "description": article["description"],
            "url": article["url"],
            "status": "expected"  # مؤقت ثابت، بعدين نضبطه للالوان
        }
    return None

# ===== إرسال الخبر في ديسكورد =====
@tasks.loop(minutes=1)
async def send_news():
    channel = bot.get_channel(CHANNEL_ID)
    news = get_news()
    if news:
        embed = discord.Embed(
            title=news["title"],
            description=news["description"],
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=LOGOS[news["status"]])
        embed.set_footer(text="GlobalPulse 🌐")
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    send_news.start()

bot.run(TOKEN)
