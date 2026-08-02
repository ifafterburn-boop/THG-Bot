import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

# ==========================
# CONFIGURATION
# ==========================
# Replace with your actual Infinite Flight API Key
IF_API_KEY = "tephscpkg4qe7xxkrfwvo9qrteksdj0l"

EMBED_COLOR = 0x57F287


class AtisCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_expert_session_id(self, session: aiohttp.ClientSession) -> str | None:
        """Fetches the active Session ID for the Expert Server."""
        url = "https://api.infiniteflight.com/public/v2/sessions"
        params = {"apikey": IF_API_KEY}
        
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("errorCode") == 0 and "result" in data:
                        for s in data["result"]:
                            # Look for Expert Server in the active sessions
                            if "expert" in s.get("name", "").lower():
                                return s.get("id")
        except Exception:
            pass
        return None

    @app_commands.command(
        name="atis",
        description="Fetch the active Expert Server ATIS for an airport in Infinite Flight."
    )
    @app_commands.describe(
        icao="The 4-letter ICAO code of the airport (e.g., EGCC, KLAX, KJFK)."
    )
    async def get_atis(
        self,
        interaction: discord.Interaction,
        icao: str
    ):
        # Acknowledge the interaction immediately to prevent timeout
        await interaction.response.defer()

        icao_code = icao.upper().strip()

        async with aiohttp.ClientSession() as session:
            # 1. Automatically fetch the Expert Server Session ID
            session_id = await self.get_expert_session_id(session)
            if not session_id:
                await interaction.followup.send(
                    "❌ Could not retrieve the **Expert Server** session. Please check your API key.",
                    ephemeral=True
                )
                return

            # 2. Query ATIS for the given airport
            url = f"https://api.infiniteflight.com/public/v2/sessions/{session_id}/airport/{icao_code}/atis"
            params = {"apikey": IF_API_KEY}

            try:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        await interaction.followup.send(
                            f"❌ API Error: HTTP {response.status}",
                            ephemeral=True
                        )
                        return

                    data = await response.json()
                    error_code = data.get("errorCode")
                    result = data.get("result")

                    # Handle API Responses
                    if error_code == 0 and result:
                        embed = discord.Embed(
                            title=f"📡 ATIS Information — {icao_code} (Expert Server)",
                            description=f"```text\n{result}\n```",
                            color=EMBED_COLOR,
                            timestamp=discord.utils.utcnow()
                        )
                        embed.set_footer(text="Infinite Flight Live API • THG Utilities")
                        
                        await interaction.followup.send(embed=embed)

                    elif error_code == 7 or result is None:
                        await interaction.followup.send(
                            f"⚠️ No active ATIS found for **{icao_code}** on the Expert Server.",
                            ephemeral=True
                        )
                    else:
                        await interaction.followup.send(
                            f"❌ Unable to fetch ATIS (Error Code: `{error_code}`).",
                            ephemeral=True
                        )

            except Exception as e:
                await interaction.followup.send(
                    f"❌ An error occurred while fetching ATIS: `{str(e)}`",
                    ephemeral=True
                )


# Setup function to load Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(AtisCog(bot))
  
