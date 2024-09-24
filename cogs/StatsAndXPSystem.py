import discord
from discord import app_commands
from discord.ext import commands, tasks
import sqlite3
import os
import asyncio
from pathlib import Path

class StatsSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_PATH = Path(r"C:\Users\shake\Documents\GitHub\BetBuddy\discord_database.db")
        self.setup_database()
        self.check_user_levels.start()  # Start task loop to check user levels

    def setup_database(self):
        # Ensure the parent directory exists before connecting to the database
        if not self.DB_PATH.parent.exists():
            self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    chips INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1
                )
            ''')
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error creating or connecting to database: {e}")

    def get_user_data(self, user_id):
        try:
            conn = sqlite3.connect(self.DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT chips, xp, level FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return result
            else:
                return None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    async def create_user(self, user_id):
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (user_id, chips, xp, level) VALUES (?, ?, ?, ?)', (user_id, 250, 0, 1))
                conn.commit()

            embed_msg = discord.Embed(title='Welcome to BetBuddy 🍒🃏', color=discord.Color.magenta())
            embed_msg.add_field(
                name='Welcome Message',
                value='Get started with `/slots`, `/blackjack`, `/roulette`, or check `/stats` and `/leaderboard`!',
                inline=False
            )
            return embed_msg
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return discord.Embed(title='Error', description='There was an error creating your profile.', color=discord.Color.red())

    def get_chip_emoji(self, chips):
        if chips > 2500:
            return "<:chips5:1278671563201445952>"
        elif chips > 1750:
            return "<:chips4:1278671577105436724>"
        elif chips > 1000:
            return "<:chips3:1278665072503160944>"
        elif chips > 225:
            return "<:chips2:1278671592444133498>"
        else:
            return "<:chips1:1278671603886194698>"

    def get_xp_for_next_level(self, level):
        level_xp_requirements = [
            100, 250, 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 
            2500, 2750, 3000, 3250, 3500, 3750, 4000, 4250, 4500, 4750, 
            5000, 5250, 5500, 5750, 6000, 6250, 6500, 6750, 7000, 7250, 
            7500, 7750, 8000, 8250, 8500, 8750, 9000, 9250, 9500, 9750, 
            10000, 10250, 10500, 10750, 11000, 11250, 11500, 11750, 12000, 12250, 
            12500, 12750, 13000, 13250, 13500, 13750, 14000, 14250, 14500, 14750, 
            15000, 15250, 15500, 15750, 16000, 16250, 16500, 16750, 17000, 17250, 
            17500, 17750, 18000, 18250, 18500, 18750, 19000, 19250, 19500, 19750
        ]
        return level_xp_requirements[level - 1] if 0 < level <= len(level_xp_requirements) else 0

    async def update_user_level(self, user_id, xp):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        user_data = self.get_user_data(user_id)
        if user_data is None:
            conn.close()
            return
        current_xp, level = user_data[1], user_data[2]
        total_xp = current_xp + xp

        while total_xp >= self.get_xp_for_next_level(level):
            total_xp -= self.get_xp_for_next_level(level)
            level += 1

            if level > 70:
                level = 70  

        cursor.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (total_xp, level, user_id))
        conn.commit()
        conn.close()

    async def check_and_update_user_level(self, user_id):
        user_data = self.get_user_data(user_id)
        if user_data:
            await self.update_user_level(user_id, 0)  

    @tasks.loop(minutes=5)  
    async def check_user_levels(self):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()

        for user_id_tuple in users:
            user_id = user_id_tuple[0]
            await self.check_and_update_user_level(user_id)

    def generate_xp_bar(self, xp, next_level_xp):
        if next_level_xp <= 0:
            return '░' * 20  
        
        total_blocks = 20  
        filled_blocks = int(total_blocks * (xp / next_level_xp))
        empty_blocks = total_blocks - filled_blocks
        xp_bar = '█' * filled_blocks + '░' * empty_blocks
        return xp_bar

    async def recompile_database(self):
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, xp, level FROM users")
        users = cursor.fetchall()
        conn.close()

        for user_id, xp, level in users:
            await self.update_user_level(user_id, 0)  

    @app_commands.command(name='stats', description='Shows the number of chips, XP, and level of a user.')
    @app_commands.describe(user='The user whose stats you want to see.')
    async def stats(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer()

        await self.recompile_database()

        if user is None:
            user = interaction.user
        user_id = user.id

        try:
            user_data = self.get_user_data(user_id)
            
            if user_data is None:
                create_profile_embed = discord.Embed(
                    title="Create Your Profile!",
                    description="It looks like you don't have a profile yet. Please create one to view your stats.",
                    color=discord.Color.red()
                )
                create_profile_embed.add_field(
                    name="To create a profile:",
                    value="Click the button below to create your profile and get started!",
                    inline=False
                )
                view = CreateAccountView(self)
                await interaction.followup.send(embed=create_profile_embed, view=view)
            else:
                chips, xp, level = user_data
                chip_emoji = self.get_chip_emoji(chips)
                next_level_xp = self.get_xp_for_next_level(level)

                if xp is None or next_level_xp is None:
                    raise ValueError("XP or next level XP is None, cannot generate XP bar")

                xp_bar = self.generate_xp_bar(xp, next_level_xp)

                embed = discord.Embed(
                    title=f"Stats for {user.display_name}",
                    color=discord.Color(0x2F3136)
                )
                embed.set_thumbnail(url=user.avatar.url if user.avatar else interaction.user.avatar.url)
                embed.add_field(name="Chips", value=f"{chips} {chip_emoji}", inline=True)
                embed.add_field(name="XP", value=f"{xp} / {next_level_xp}", inline=True)
                embed.add_field(name="Level", value=str(level), inline=True)
                embed.add_field(name="XP Bar", value=xp_bar, inline=False)

                await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"Error in /stats command: {e}")
            await interaction.followup.send("An error occurred while fetching your stats.", ephemeral=True)

class CreateAccountView(discord.ui.View):
    def __init__(self, cog_instance):
        super().__init__()
        self.cog_instance = cog_instance

    @discord.ui.button(label='Create a Profile', style=discord.ButtonStyle.green, custom_id='create_profile')
    async def create_profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        embed = await self.cog_instance.create_user(user_id)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatsSystem(bot))
