import discord
from discord.ext import commands, tasks


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_loop.start()

    def cog_unload(self):
        self.status_loop.cancel()

    @tasks.loop(seconds=15)
    async def status_loop(self):
        activities = [
            discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.bot.guilds)} Servers"
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="/help"
            ),
            discord.Game("THG Utilities"),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="Made with discord.py"
            ),
        ]

        activity = activities[self.status_loop.current_loop % len(activities)]

        await self.bot.change_presence(
            status=discord.Status.online,
            activity=activity
        )

    @status_loop.before_loop
    async def before_status(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Status(bot))
