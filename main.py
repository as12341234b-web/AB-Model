import discord
from discord.ext import commands
import os

# قراءة التوكن من المتغيرات البيئية (Environment Variables)
TOKEN = os.getenv("DISCORD_TOKEN")

# إعداد البوت
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("هلا! البوت شغال 🔥")

bot.run(TOKEN)
