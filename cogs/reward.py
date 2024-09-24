import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import asyncio
from datetime import datetime, timedelta

class RewardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_PATH = r"C:\Users\Fatek\Documents\GitHub\BetBuddy\discord_database.db"

    @app_commands.command(name='daily', description='Claim your daily reward of 200 chips.')
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if not self.user_exists(user_id):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='No Profile',
                    description="You don't have a profile. Please create one first.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        last_reward = self.get_user_last_reward(user_id)
        now = datetime.utcnow()

        if last_reward is None or now - datetime.fromisoformat(last_reward) >= timedelta(days=1):
            new_chip_count = self.add_chips(user_id, 200)
            self.update_last_reward(user_id, now.isoformat())
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Daily Reward',
                    description=f"You have received 200 chips {self.get_chip_emoji(new_chip_count)}. Your new balance is {new_chip_count} chips.",
                    color=discord.Color(0x2F3136)
                )
            )
        else:
            next_reward_time = datetime.fromisoformat(last_reward) + timedelta(days=1)
            wait_time = (next_reward_time - now).total_seconds()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Daily Reward',
                    description=f"You have already claimed your reward. Please wait {int(wait_time // 3600)} hours and {int((wait_time % 3600) // 60)} minutes before claiming again.",
                    color=discord.Color.red()
                )
            )

    @app_commands.command(name='claim', description='Claim your reward of 10 chips every 5 minutes.')
    async def claim(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if not self.user_exists(user_id):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='No Profile',
                    description="You don't have a profile. Please create one first.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        last_claim = self.get_user_last_claim(user_id)
        now = datetime.utcnow()

        if last_claim is None or now - datetime.fromisoformat(last_claim) >= timedelta(minutes=5):
            new_chip_count = self.add_chips(user_id, 10)
            self.update_last_claim(user_id, now.isoformat())
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Claim Reward',
                    description=f"You have received 10 chips {self.get_chip_emoji(new_chip_count)}. Your new balance is {new_chip_count} chips.",
                    color=discord.Color(0x2F3136)
                )
            )
        else:
            next_claim_time = datetime.fromisoformat(last_claim) + timedelta(minutes=5)
            wait_time = (next_claim_time - now).total_seconds()
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Claim Reward',
                    description=f"You have already claimed your reward. Please wait {int(wait_time // 60)} minutes and {int(wait_time % 60)} seconds before claiming again.",
                    color=discord.Color.red()
                )
            )

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

    def get_user_chips_and_reward_time(self, user_id):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT chips, last_reward FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            if result:
                return result
            else:
                return (0, None)
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return (0, None)

    def get_user_last_reward(self, user_id):
        _, last_reward = self.get_user_chips_and_reward_time(user_id)
        return last_reward

    def get_user_last_claim(self, user_id):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT last_claim FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def add_chips(self, user_id, amount):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET chips = chips + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            cursor.execute("SELECT chips FROM users WHERE user_id = ?", (user_id,))
            new_chip_count = cursor.fetchone()[0]
            conn.close()
            return new_chip_count
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0

    def update_last_reward(self, user_id, reward_time):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_reward = ? WHERE user_id = ?", (reward_time, user_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def update_last_claim(self, user_id, claim_time):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_claim = ? WHERE user_id = ?", (claim_time, user_id))
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

    async def create_user(self, user_id):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (user_id, chips, last_reward, last_claim) VALUES (?, ?, ?, ?)', (user_id, 250, None, None))
            conn.commit()
            conn.close()
            embed_msg = discord.Embed(title='New profile created!', color=discord.Color.magenta())
            embed_msg.add_field(name='Try these commands:', value='**/blackjack**\n**/daily**\n**/roulette**')
            return embed_msg
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return discord.Embed(title='Error', description='There was an error creating your profile.', color=discord.Color.red())

    async def delete_message_after_delay(self, message, delay):
        """Delete the message after a specified delay."""
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except discord.NotFound:
            pass

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

async def setup(bot):
    await bot.add_cog(RewardCog(bot))
