import os
import discord
from discord.ext import commands, tasks
import requests

# ===== إعدادات البوت =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # حط التوكن حق البوت في إعدادات Render/GitHub Secrets
CHANNEL_ID = 123456789012345678  # اكتب هنا ID القناة اللي تبغى ينزل فيها الخبر

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== روابط اللوجو حسب نوع الخبر =====
LOGOS = {
    "higher": "https://link-to-green-logo.png",
    "lower": "https://link-to-red-logo.png",
    "expected": "https://link-to-blue-logo.png"
}

# ===== جلب الأخبار من API (مثال) =====
def get_news():
    # هذا مجرد مثال باستخدام API تجريبي (تحط API حقيقي زي ForexFactory/Investing)
    response = requests.get("https://newsapi.org/v2/top-headlines?category=business&apiKey=YOUR_API_KEY")
    data = response.json()
    if "articles" in data and len(data["articles"]) > 0:
        article = data["articles"][0]
        return {
            "title": article["title"],
            "description": article["description"],
            "url": article["url"],
            "status": "expected"  # مؤقتاً ثابت، بعدين نخليه يتحكم باللون (أعلى/أقل/متوقع)
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
        embed.set_thumbnail(url=LOGOS[news["status"]])  # يغير اللوجو حسب الخبر
        embed.set_footer(text="GlobalPulse 🌐")  # التوقيع أسفل الخبر
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    send_news.start()

bot.run(TOKEN)
