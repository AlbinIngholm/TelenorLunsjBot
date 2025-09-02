import os
import random
import asyncio
from datetime import datetime
import zoneinfo
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from scraper import fetch_lunch_menu  # your scraper.py

load_dotenv()

# Configuration from .env
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("LUNCH_CHANNEL_ID"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Oslo")

# Emojis for each restaurant
RESTAURANT_EMOJIS = {
    "Eat The Street": "🍕",
    "Flow": "🍲",
    "Fresh 4 You": "🥗"
}

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="*", intents=intents)

# Timezone for scheduling
tz = zoneinfo.ZoneInfo(TIMEZONE)
last_posted_week = None
ping_day_of_week = random.randint(0, 4)  # 0 = Monday, 4 = Friday

# Format lunch menu nicely
def format_lunch_menu(menu: dict) -> str:
    message = "**Dagens lunsj:**\n\n"
    for restaurant, items in menu.items():
        message += f"**{restaurant} {RESTAURANT_EMOJIS.get(restaurant, '')}:**\n"
        for item in items:
            message += f"• {item}\n"
        message += "\n"
    return message

# Automatic weekly lunch posting
@tasks.loop(minutes=15)
async def lunch_task():
    global last_posted_week, ping_day_of_week
    now = datetime.now(tz)

    # Skip weekends
    if now.weekday() >= 5:
        return

    # Only post once per week on the random weekday
    if now.isocalendar().week != last_posted_week and now.weekday() == ping_day_of_week:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            print(f"Channel {CHANNEL_ID} not found")
            return

        try:
            menu = await fetch_lunch_menu()
        except Exception as e:
            print(f"Failed to fetch menu: {e}")
            return

        message_text = f"@everyone\n{format_lunch_menu(menu)}"
        try:
            message = await channel.send(message_text)
            # Add reactions for voting
            for restaurant, emoji in RESTAURANT_EMOJIS.items():
                await message.add_reaction(emoji)
        except discord.Forbidden:
            print("Bot lacks permission to send messages or add reactions.")
        except Exception as e:
            print(f"Error sending message: {e}")

        last_posted_week = now.isocalendar().week
        ping_day_of_week = random.randint(0, 4)  # pick new day for next week

# Manual command to post lunch menu
@bot.command(name="lunch")
async def lunch_command(ctx):
    """Manually post the lunch menu in the configured channel."""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        await ctx.send(f"Configured channel with ID {CHANNEL_ID} not found.")
        return

    try:
        menu = await fetch_lunch_menu()
    except Exception as e:
        await ctx.send(f"Failed to fetch lunch menu: {e}")
        return

    formatted = format_lunch_menu(menu)
    message = await channel.send(formatted)

    poll_message = await channel.send("Hvor vil vi spise lunsj i dag? Reager med emoji:")
    for restaurant, emoji in RESTAURANT_EMOJIS.items():
        await poll_message.add_reaction(emoji)

    await ctx.send(f"Lunch menu posted in {channel.mention}!")

# Bot startup
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    lunch_task.start()

bot.run(TOKEN)
