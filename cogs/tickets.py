import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import asyncio

# ==========================
# CONFIG
# ==========================

SUPPORT_ROLE_ID = 1307299081676263444
CATEGORY_ID = 1341446337475903511
LOG_CHANNEL_ID = 1474218472929235026
PANEL_CHANNEL_ID = 1341446676443041862

EMBED_COLOR = 0x57F287


# ==========================
# CREATE TICKET BUTTON
# ==========================

class CreateTicketView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Create Ticket",
        emoji="📩",
        style=discord.ButtonStyle.green,
        custom_id="create_ticket"
    )
    async def create_ticket(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        guild = interaction.guild
        member = interaction.user

        support_role = guild.get_role(SUPPORT_ROLE_ID)
        category = guild.get_channel(CATEGORY_ID)

        # Prevent duplicate tickets
        existing = find_existing_ticket(category, member.id)

        if existing:
            await interaction.response.send_message(
                f"❌ You already have an open ticket:\n{existing.mention}",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            ),
            support_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_messages=True,
                manage_channels=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True
            )
        }

        channel = await guild.create_text_channel(
            name=get_ticket_name(),
            category=category,
            overwrites=overwrites,
            topic=str(member.id)
        )

        embed = discord.Embed(
            title="🎫 THG Utilities Support",
            description=(
                f"Welcome {member.mention}!\n\n"
                "Thank you for opening a support ticket.\n"
                "Please describe your issue in as much detail as possible.\n\n"
                "A member of our support team will assist you shortly."
            ),
            color=EMBED_COLOR
        )

        embed.add_field(
            name="📋 Ticket Information",
            value=(
                f"**User:** {member.mention}\n"
                f"**Ticket ID:** `{channel.name}`\n"
                f"**Status:** 🟢 Open"
            ),
            inline=False
        )

        embed.add_field(
            name="📜 Rules",
            value=(
                "• Be respectful.\n"
                "• Do not spam or ping staff.\n"
                "• Stay on the topic of this ticket."
            ),
            inline=False
        )

        embed.set_footer(
            text="THG Utilities • Support System"
        )

        await channel.send(
            content=f"{member.mention} {support_role.mention}",
            embed=embed
        )

        await interaction.response.send_message(
            f"✅ Your ticket has been created: {channel.mention}",
            ephemeral=True
        )


# ==========================
# TICKET PANEL COMMAND
# ==========================

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Persistent View
        self.bot.add_view(CreateTicketView(bot))

    @app_commands.command(
        name="ticketpanel",
        description="Send the ticket support panel."
    )
    @app_commands.default_permissions(administrator=True)
    async def ticketpanel(self, interaction: discord.Interaction):
        panel_channel = interaction.guild.get_channel(PANEL_CHANNEL_ID)

        if panel_channel is None:
            await interaction.response.send_message(
                "❌ Panel channel not found.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎫 THG Utilities Support Center",
            description=(
                "Welcome to the **THG Utilities Support Center**.\n\n"
                "Need assistance?\n"
                "Click the **Create Ticket** button below.\n\n"
                "**Before opening a ticket:**\n"
                "• Explain your issue clearly.\n"
                "• Be respectful to staff.\n"
                "• One ticket per issue.\n"
                "• Don't spam or ping staff.\n"
                "• False tickets may result in punishment."
            ),
            color=EMBED_COLOR
        )

        embed.add_field(
            name="📂 Available Support",
            value=(
                "🛠 General Support\n"
                "🤖 Bot Support\n"
                "🐞 Bug Reports\n"
                "🤝 Partnership\n"
                "⚠ Staff Reports"
            ),
            inline=False
        )

        embed.add_field(
            name="⏱ Response Time",
            value=(
                "🟢 Usually within **15 minutes**.\n"
                "Please be patient while waiting."
            ),
            inline=False
        )

        embed.add_field(
            name="📜 Ticket Rules",
            value=(
                "• One ticket at a time.\n"
                "• Don't troll.\n"
                "• Respect everyone.\n"
                "• Stay on topic."
            ),
            inline=False
        )

        embed.set_footer(
            text="THG Utilities • Professional Ticket System"
        )

        embed.set_thumbnail(
            url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty
        )

        await panel_channel.send(
            embed=embed,
            view=CreateTicketView(self.bot)
        )

        await interaction.response.send_message(
            "✅ Ticket panel sent successfully.",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_ready(self):
        print("✅ Tickets Cog Loaded")


# ==========================
# HELPER FUNCTIONS
# ==========================

ticket_counter = 1


def get_ticket_name():
    global ticket_counter
    name = f"ticket-{ticket_counter:04d}"
    ticket_counter += 1
    return name


def find_existing_ticket(category, user_id):
    for channel in category.text_channels:
        if channel.topic == str(user_id):
            return channel
    return None


# ==========================
# COG SETUP
# ==========================

async def setup(bot):
    await bot.add_cog(Tickets(bot))
