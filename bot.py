import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("MTUzMjc4NDUxNjY3NzExMTk1OQ.G3C1Bk.HiXa_t7hcxponPsNApuWG6sw5NEnfVe09D9Ui4")

# Configure intents
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

# Create bot instance
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# Load all cogs
async def load_cogs():
    if not os.path.exists("cogs"):
        os.makedirs("cogs")

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✓ Loaded {filename}")
            except Exception as e:
                print(f"✗ Failed to load {filename}: {e}")

# Ready event
@bot.event
async def on_ready():
    print("=" * 40)
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Servers: {len(bot.guilds)}")
    print("=" * 40)

    try:
        synced = await bot.tree.sync()
        print(f"✓ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Sync failed: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
