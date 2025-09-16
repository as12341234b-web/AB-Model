# main.py
import os
import logging
from datetime import datetime, timedelta, timezone
import requests
from bs4 import BeautifulSoup
from dateutil import parser
import pytz
import discord
from discord.ext import tasks, commands

# ------------------ إعداد اللوج ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ------------------ إعدادات من البيئة ----------
TOKEN = os.getenv("DISCORD_TOKEN")  # لازم تحطه في Render
ROOM_ID = int(os.getenv("ROOM_ID", "1417061905423667301"))  # روم الأخبار
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # معرف مالك البوت

# ⏰ التوقيت مضبوط على 12:00 ليل الرياض
SA_TZ = pytz.timezone("Asia/Riyadh")
SEND_HOUR_LOCAL = 0
SEND_MINUTE_LOCAL = 0

# الهوية والعلامة
BRAND_NAME = "GP🌐 News"
BRAND_SIGN = "GlobalPuls🌐e"

FF_CALENDAR_URL = "https://www.forexfactory.com/calendar.php"
MAX_NEWS = 30

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

NY_TZ = pytz.timezone("America/New_York")

# ------------------ جلب صفحة ForexFactory ----------
def fetch_ff_calendar_html():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GPNewsBot/1.0; +https://example.com/)"
    }
    r = requests.get(FF_CALENDAR_URL, headers=headers, timeout=25)
    r.raise_for_status()
    return r.text

# ------------------ تحليل الصفحة ----------
def parse_ff_events(html):
    soup = BeautifulSoup(html, "html.parser")
    events = []
    rows = soup.select("tr.calendar__row") or soup.select("tr.calendar_row") or soup.select("tr")
    for r in rows:
        try:
            title_el = r.select_one(".calendar__event, .event, td.event, .title")
            title = title_el.get_text(strip=True) if title_el else None
            if not title:
                continue

            impact_el = r.select_one(".impact, .calendar__impact, td.impact")
            impact = ""
            if impact_el:
                impact = (impact_el.get("title") or impact_el.get("alt") or impact_el.get_text(strip=True)).strip()

            time_el = r.select_one(".calendar__time, td.time, .time")
            time_text = time_el.get_text(strip=True) if time_el else ""

            actual = forecast = previous = "-"
            vals = r.select(".actual, .forecast, .previous, td.actual, td.forecast, td.previous")
            if vals and len(vals) >= 3:
                actual = vals[0].get_text(strip=True)
                forecast = vals[1].get_text(strip=True)
                previous = vals[2].get_text(strip=True)

            link_el = r.select_one("a[href^='http']")
            official_link = link_el.get("href") if link_el else None

            dt_utc = None
            if time_text:
                try:
                    dt_parsed = parser.parse(time_text, fuzzy=True)
                    if dt_parsed.year == 1900:
                        today = datetime.utcnow()
                        dt_parsed = dt_parsed.replace(year=today.year, month=today.month, day=today.day)
                    if dt_parsed.tzinfo is None:
                        dt_utc = dt_parsed.replace(tzinfo=timezone.utc)
                    else:
                        dt_utc = dt_parsed.astimezone(timezone.utc)
                except Exception:
                    dt_utc = None

            events.append({
                "title": title,
                "time_utc": dt_utc,
                "impact": impact or "",
                "official_link": official_link,
                "actual": actual,
                "forecast": forecast,
                "previous": previous,
            })
        except Exception:
            continue
    return events

# ------------------ اختيار الأخبار ----------
def select_top_events(events, max_count=MAX_NEWS):
    high = [e for e in events if "high" in e.get("impact", "").lower()]
    medium = [e for e in events if "medium" in e.get("impact", "").lower()]
    def time_key(e): return e.get("time_utc") or datetime.max.replace(tzinfo=timezone.utc)
    high.sort(key=time_key)
    medium.sort(key=time_key)
    selected = high[:max_count]
    if len(selected) < max_count:
        selected += medium[:max_count - len(selected)]
    return selected[:max_count]

# ------------------ تنسيقات الوقت ----------
def format_times_and_countdown(event_dt_utc):
    if not event_dt_utc:
        return ("--:--:--", "--:--:--", "--:--:--")
    dt_utc = event_dt_utc.astimezone(timezone.utc)
    dt_ny = dt_utc.astimezone(NY_TZ)
    dt_sa = dt_utc.astimezone(SA_TZ)
    now_utc = datetime.now(timezone.utc)
    delta = dt_utc - now_utc
    if delta.total_seconds() <= 0:
        countdown = "00:00:00"
    else:
        total = int(delta.total_seconds())
        hh = total // 3600
        mm = (total % 3600) // 60
        ss = total % 60
        countdown = f"{hh:02d}:{mm:02d}:{ss:02d}"
    return (dt_ny.strftime("%I:%M:%S %p"), dt_sa.strftime("%I:%M:%S %p"), countdown)

# ------------------ بناء الرسالة ----------
def build_daily_message(events):
    lines = []
    for idx, e in enumerate(events, start=1):
        title = e.get("title", "—")
        dt = e.get("time_utc")
        ny_time, sa_time, countdown = format_times_and_countdown(dt)
        actual = e.get("actual") or "-"
        forecast = e.get("forecast") or "-"
        previous = e.get("previous") or "-"
        official = e.get("official_link") or ""
        source_display = f"[{BRAND_NAME}]({official})" if official else BRAND_NAME
        date_str = dt.strftime("%d-%m-%Y") if dt else datetime.utcnow().strftime("%d-%m-%Y")

        block = (
            f"[{idx}] 🗓 التاريخ: {date_str}\n"
            f"⏰ موعد صدور الخبر | News Release Time\n"
            f"🕒 الوقت (نيويورك): {ny_time}\n"
            f"🕒 الوقت (السعودية): {sa_time}\n"
            f"⏳ يتبقى على صدور الخبر: {countdown}\n\n"
            f"خبر عاجل: {title}\n"
            f"المصدر الرسمي: {source_display}\n\n"
            f"📊 النتيجة الفعلية: {actual}\n"
            f"📈 المتوقَّع: {forecast}\n"
            f"📉 السابق: {previous}\n\n"
            f"🔎 التأثير: {e.get('impact','-')}\n"
            f"{BRAND_SIGN}\n"
        )
        lines.append(block)
    return "\n".join(lines)

# ------------------ إرسال الأخبار ----------
async def publish_news_batch():
    try:
        html = fetch_ff_calendar_html()
        events = parse_ff_events(html)
        selected = select_top_events(events, max_count=MAX_NEWS)
        if not selected:
            return
        message_text = build_daily_message(selected)
        channel = bot.get_channel(ROOM_ID)
        if not channel:
            return
        max_chunk = 1900
        if len(message_text) <= max_chunk:
            await channel.send(message_text)
        else:
            parts, cur = [], ""
            for block in message_text.split("\n\n"):
                block_with_sep = block + "\n\n"
                if len(cur) + len(block_with_sep) > max_chunk:
                    parts.append(cur)
                    cur = block_with_sep
                else:
                    cur += block_with_sep
            if cur: parts.append(cur)
            header = f"🔔 {BRAND_NAME} — دفعة أخبار اليوم — {datetime.utcnow().strftime('%d-%m-%Y')}\n\n"
            await channel.send(header)
            for p in parts:
                await channel.send(p)
    except Exception as e:
        logging.exception("publish_news_batch error: %s", e)

# ------------------ مهمة الجدولة ----------
@tasks.loop(seconds=60)
async def schedule_checker():
    try:
        now_sa = datetime.now(SA_TZ)
        if now_sa.hour == SEND_HOUR_LOCAL and now_sa.minute == SEND_MINUTE_LOCAL:
            await publish_news_batch()
            await discord.utils.sleep_until(datetime.now(timezone.utc) + timedelta(seconds=90))
    except Exception:
        logging.exception("schedule_checker error")

# ------------------ أوامر يدوية ----------
@bot.command()
async def publish_now(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ ما عندك صلاحية تستخدم هذا الأمر.")
    await ctx.send("⏳ نشر الأخبار يدويًا...")
    await publish_news_batch()
    await ctx.send("✅ انتهى.")

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    if not schedule_checker.is_running():
        schedule_checker.start()

if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN required")
    bot.run(TOKEN)
