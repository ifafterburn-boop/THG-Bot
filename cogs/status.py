import discord
from discord.ext import commands
from discord import app_commands

class StatusDropdown(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot

        options = [
            discord.SelectOption(
                label="Playing",
                description="Set Playing status",
                emoji="🎮"
            ),
            discord.SelectOption(
                label="Watching",
                description="Set Watching status",
                emoji="👀"
            ),
            discord.SelectOption(
                label="Listening",
                description="Set Listening status",
                emoji="🎧"
            ),
            discord.SelectOption(
                label="Competing",
                description="Set Competing status",
                emoji="🏆"
            ),
        ]

        super().__init__(
            placeholder="Choose a status...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "Playing":
            activity = discord.Game("THG Utilities")

        elif self.values[0] == "Watching":
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="your server"
            )

        elif self.values[0] == "Listening":
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name="/help"
            )

        else:
            activity = discord.Activity(
                type=discord.ActivityType.competing,
                name="Discord"
            )

        await self.bot.change_presence(
            status=discord.Status.online,
            activity=activity
        )

        await interaction.response.send_message(
            f"✅ Status changed to **{self.values[0]}**",
            ephemeral=True
        )


class StatusView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(StatusDropdown(bot))


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="setstatus",
        description="Change the bot status"
    )
    @app_commands.default_permissions(administrator=True)
    async def setstatus(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Select a status below:",
            view=StatusView(self.bot),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Status(bot))
