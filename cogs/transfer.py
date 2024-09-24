import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import asyncio

class ChipTransferCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_PATH = r"C:\Users\Fatek\Documents\GitHub\BetBuddy\discord_database.db"

    @app_commands.command(name='transfer', description='Transfer chips to another user.')
    async def send_chips(self, interaction: discord.Interaction, recipient: discord.User, amount: int, comment: str = None):
        sender_id = interaction.user.id
        recipient_id = recipient.id

        if not self.user_exists(sender_id):
            await interaction.response.send_message(embed=self.error_embed("You don't have a profile yet. Please create one first."), ephemeral=True)
            return

        if not self.user_exists(recipient_id):
            await interaction.response.send_message(embed=self.error_embed("The recipient doesn't have a profile."), ephemeral=True)
            return

        sender_chips = self.get_user_chips(sender_id)
        if sender_chips < amount:
            await interaction.response.send_message(embed=self.error_embed("You don't have enough chips to complete this transaction."), ephemeral=True)
            return

        self.update_user_chips(sender_id, -amount)
        self.update_user_chips(recipient_id, amount)


        chip_emoji = self.get_chip_emoji(amount)

        success_embed = discord.Embed(title="Chip Transfer", color=discord.Color(0x2F3136))
        success_embed.add_field(name="Sender", value=f"{interaction.user.display_name}", inline=True)
        success_embed.add_field(name="Recipient", value=f"{recipient.display_name}", inline=True)
        success_embed.add_field(name="Amount", value=f"{amount} {chip_emoji}", inline=True)
        if comment:
            success_embed.add_field(name="Comment", value=comment, inline=False)
        
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

        recipient_embed = discord.Embed(title="You've Received Chips!", color=discord.Color.gold())
        recipient_embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
        recipient_embed.add_field(name="From", value=f"{interaction.user.display_name}", inline=True)
        recipient_embed.add_field(name="Amount", value=f"{amount} {chip_emoji}", inline=True)
        if comment:
            recipient_embed.add_field(name="Comment", value=comment, inline=False)
        else:
            recipient_embed.add_field(name="Comment", value="No comment provided.", inline=False)
        
        await recipient.send(embed=recipient_embed)

    def user_exists(self, user_id):
        """Check if a user exists in the database."""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_user_chips(self, user_id):
        """Get the number of chips a user has."""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT chips FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0

    def update_user_chips(self, user_id, amount):
        """Update the number of chips a user has."""
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET chips = chips + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def get_chip_emoji(self, chips):
        """Return the appropriate chip emoji based on the number of chips."""
        if chips > 2500:
            return "<:chips5:1278671563201445952>"
        elif chips > 1750:
            return "<:chips4:1278671577105436724>"
        elif chips > 1000:
            return "<:chips3:1278665072503160944>"
        elif chips > 200:
            return "<:chips2:1278671592444133498>"
        else:
            return "<:chips1:1278671603886194698>"

    def error_embed(self, message: str):
        """Create an embed for error messages."""
        embed = discord.Embed(title="Error", description=message, color=discord.Color.red())
        return embed

async def setup(bot):
    await bot.add_cog(ChipTransferCog(bot))
