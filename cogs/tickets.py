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
# TICKET ACTIONS VIEW (Claim & Close)
# ==========================

class TicketActionsView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Claim Ticket",
        emoji="🙋",
        style=discord.ButtonStyle.blurple,
        custom_id="claim_ticket"
    )
    async def claim_ticket(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        # Always acknowledge interactions right away to prevent "didn't respond" timeouts
        await interaction.response.defer(ephemeral=True)

        # Only support role can claim
        support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
        if not support_role or support_role not in interaction.user.roles:
            await interaction.followup.send(
                "❌ Only support staff can claim tickets.",
                ephemeral=True
            )
            return

        # Fetch message and update embed
        message = interaction.message
        if message.embeds:
            embed = message.embeds[0]
            new_embed = discord.Embed.from_dict(embed.to_dict())
            
            # Check if ticket is already claimed
            for i, field in enumerate(new_embed.fields):
                if field.name == "📋 Ticket Information":
                    if "Claimed by" in field.value:
                        await interaction.followup.send("❌ This ticket is already claimed!", ephemeral=True)
                        return
                    
                    value = field.value.replace("🟢 Open", f"🙋 Claimed by {interaction.user.mention}")
                    new_embed.set_field_at(i, name="📋 Ticket Information", value=value, inline=False)
                    break

            await message.edit(embed=new_embed)
            await interaction.followup.send(
                f"✅ Ticket successfully claimed by {interaction.user.mention}!",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            "❌ Could not claim ticket.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Close Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.red,
        custom_id="close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
        channel = interaction.channel
        
        ticket_owner_id = int(channel.topic) if channel.topic and channel.topic.isdigit() else None
        
        is_support = support_role in interaction.user.roles if support_role else False
        is_owner = ticket_owner_id == interaction.user.id
        
        if not is_support and not is_owner:
            await interaction.response.send_message(
                "❌ You don't have permission to close this ticket.",
                ephemeral=True
            )
            return

        # Send confirmation view
        confirm_view = ConfirmCloseView(self.bot)
        await interaction.response.send_message(
            "⚠️ Are you sure you want to close this ticket?",
            view=confirm_view,
            ephemeral=True
        )


# ==========================
# CONFIRM CLOSE VIEW
# ==========================

class ConfirmCloseView(View):
    def __init__(self, bot):
        super().__init__(timeout=30)
        self.bot = bot

    @discord.ui.button(
        label="Yes, Close",
        emoji="✅",
        style=discord.ButtonStyle.danger,
        custom_id="confirm_close"
    )
    async def confirm_close(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        # Acknowledge immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel
        member_id = int(channel.topic) if channel.topic and channel.topic.isdigit() else None
        
        # Log entry
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        log_embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=(
                f"**Ticket:** {channel.name}\n"
                f"**Closed by:** {interaction.user.mention}\n"
                f"**User:** <@{member_id}>" if member_id else "**User:** Unknown"
            ),
            color=0xED4245,
            timestamp=discord.utils.utcnow()
        )
        
        if log_channel:
            await log_channel.send(embed=log_embed)
        
        # Disable channel permissions for ticket owner & default role
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        if member_id:
            member = interaction.guild.get_member(member_id)
            if member:
                await channel.set_permissions(member, view_channel=False)

        # Notify inside channel and update status
        await interaction.followup.send("🔒 Ticket is being closed and will be deleted in 15 seconds.", ephemeral=True)

        # Rename channel
        if not channel.name.startswith("closed-"):
            await channel.edit(name=f"closed-{channel.name}")

        # Delete after 15 seconds delay
        await asyncio.sleep(15)
        await channel.delete()

    @discord.ui.button(
        label="Cancel",
        emoji="❌",
        style=discord.ButtonStyle.grey,
        custom_id="cancel_close"
    )
    async def cancel_close(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        await interaction.response.edit_message(
            content="✅ Ticket close cancelled.",
            view=None
        )


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
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = interaction.user

        support_role = guild.get_role(SUPPORT_ROLE_ID)
        category = guild.get_channel(CATEGORY_ID)

        # Prevent duplicate tickets
        existing = find_existing_ticket(category, member.id) if category else None

        if existing:
            await interaction.followup.send(
                f"❌ You already have an open ticket:\n{existing.mention}",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True
            )
        }

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_messages=True,
                manage_channels=True,
                read_message_history=True
            )

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

        embed.set_footer(text="THG Utilities • Support System")

        content_ping = f"{member.mention} {support_role.mention}" if support_role else f"{member.mention}"

        await channel.send(
            content=content_ping,
            embed=embed,
            view=TicketActionsView(self.bot)
        )

        await interaction.followup.send(
            f"✅ Your ticket has been created: {channel.mention}",
            ephemeral=True
        )


# ==========================
# TICKET PANEL COMMAND
# ==========================

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Register persistent views globally
        self.bot.add_view(CreateTicketView(bot))
        self.bot.add_view(TicketActionsView(bot))

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

        embed.set_footer(text="THG Utilities • Professional Ticket System")

        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

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
    if not category:
        return None
    for channel in category.text_channels:
        if channel.topic == str(user_id):
            return channel
    return None


# ==========================
# COG SETUP
# ==========================

async def setup(bot):
    await bot.add_cog(Tickets(bot))
        
