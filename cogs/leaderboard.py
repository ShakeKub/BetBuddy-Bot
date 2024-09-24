import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import asyncio

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_PATH = r"C:\Users\Fatek\Documents\GitHub\BetBuddy\discord_database.db"

    @app_commands.command(name='leaderboard', description='Displays the top 5 richest users.')
    async def leaderboard(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if not self.user_exists(user_id):
            view = CreateAccountView(self)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='No Profile',
                    description="It looks like this user doesn't have an account. Please create one by clicking the button below!",
                    color=discord.Color(0x2F3136)
                ),
                view=view,
                ephemeral=True
            )
            return

        leaderboard_data = self.get_leaderboard_data()

        if not leaderboard_data:
            await interaction.response.send_message("No data available for the leaderboard.", ephemeral=True)
            return
        
        embed = discord.Embed(title="Leaderboard - Top 5 Richest Users", color=discord.Color(0x2F3136))

        for idx, (user_id, chips, level) in enumerate(leaderboard_data):
            user = await self.bot.fetch_user(user_id)
            chip_emoji = self.get_chip_emoji(chips)

            embed.add_field(
                name=f"{idx + 1}. {user.display_name}  [Level {level}]",
                value=f"{chips} {chip_emoji}",
                inline=False
            )

            if user_id == interaction.user.id:
                embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        
        message = await interaction.response.send_message(embed=embed)
        await self.delete_message_after_delay(message, 20)

    def get_leaderboard_data(self):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, chips, level FROM users ORDER BY chips DESC LIMIT 5")
            result = cursor.fetchall()
            conn.close()
            return result
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

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

    async def delete_message_after_delay(self, message, delay):
        """Delete the message after a specified delay."""
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except discord.NotFound:
            pass

    def user_exists(self, user_id):
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

    async def create_user(self, user_id):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (user_id, chips, level, last_reward, last_claim) VALUES (?, ?, ?, ?, ?)', (user_id, 250, 1, None, None))
            conn.commit()
            conn.close()
            embed_msg = discord.Embed(title='New profile created!', color=discord.Color.magenta())
            embed_msg.add_field(name='Try these commands:', value='**/blackjack**\n**/daily**\n**/roulette**')
            return embed_msg
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return discord.Embed(title='Error', description='There was an error creating your profile.', color=discord.Color.red())

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))

class CreateAccountView(discord.ui.View):
    def __init__(self, cog_instance):
        super().__init__()
        self.cog_instance = cog_instance

    @discord.ui.button(label='Create a Profile', style=discord.ButtonStyle.green)
    async def create_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cog_instance.user_exists(interaction.user.id):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Profile Exists',
                    description="You already have a profile.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        else:
            embed_msg = await self.cog_instance.create_user(interaction.user.id)
            message = await interaction.response.send_message(embed=embed_msg)
            await self.cog_instance.delete_message_after_delay(message, 30)
