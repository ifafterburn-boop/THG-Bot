import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TOKEN")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Bot
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# Load all cogs
async def load_cogs():
    print("⚙️ Loading cogs...")

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")


@bot.event
async def on_connect():
    print("🔄 Connected to Discord...")


@bot.event
async def on_ready():
    print("=" * 40)
    print(f"✅ Logged in as {bot.user}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"🌐 Servers: {len(bot.guilds)}")
    print("=" * 40)

    # Sync global slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} global command(s).")
    except Exception as e:
        print(f"❌ Sync failed: {e}")


@bot.tree.command(name="test", description="Test slash command")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(
        "✅ Slash commands are working!"
    )


async def main():
    async with bot:
        await load_cogs()

        if TOKEN:
            await bot.start(TOKEN)
        else:
            print("❌ TOKEN environment variable not found!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
