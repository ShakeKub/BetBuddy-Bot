import discord
from discord.ext import commands
import random
from discord.ui import Button, View
import sqlite3
import asyncio

class CaseGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                chips INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    async def open_case(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT chips FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result is None:
            await interaction.response.send_message("You are not registered. Please register first.")
            return

        current_chips = result[0]

        if current_chips < 250:
            await interaction.response.send_message("You do not have enough chips to open a case. Please earn or deposit more chips.")
            return

        confirm_embed = discord.Embed(
          title="Open a Case?",
          description=(
        "It will cost **250 <:chips4:1278671577105436724>** to open this case. Are you sure you want to proceed?\n\n"
        "**Price List:**\n"
        "🍎 75 <:chips2:1278671592444133498>\n"
        "🍌 175 <:chips2:1278671592444133498>\n"
        "🍇 350 <:chips3:1278665072503160944>\n"
        "🍉 1250 <:chips4:1278671577105436724>\n"
        "🍍 2500 <:chips4:1278671577105436724>\n"
        "🍈 13000 <:chips5:1278671563201445952>"
       ),
          color=0x2F3136
)

        confirm_view = View(timeout=30)
        confirm_button = Button(label="Confirm", style=discord.ButtonStyle.success, custom_id="confirm_open")
        cancel_button = Button(label="Cancel", style=discord.ButtonStyle.danger, custom_id="cancel_open")
        confirm_view.add_item(confirm_button)
        confirm_view.add_item(cancel_button)

        await interaction.response.send_message(embed=confirm_embed, view=confirm_view)
        message = await interaction.original_response()

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=30.0, check=check)
            if inter.data['custom_id'] == "confirm_open":
                await inter.response.defer()
                await self.start_spinning(interaction, message)
            else:
                await inter.response.defer()
                await message.delete()

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def start_spinning(self, interaction: discord.Interaction, message):
        await message.edit(view=None)

        emotes = [
            ("🍎", 50),   
            ("🍌", 27),   
            ("🍇", 13),  
            ("🍉", 5),   
            ("🍍", 2),    
            ("🍈", 0.1)   
        ]

        spin_sequence = random.choices(
            [emote for emote, _ in emotes],
            [weight for _, weight in emotes],
            k=11
        )

        black_square = ":black_medium_small_square: "
        pointer = "🔻"
        pointe2 = ":small_red_triangle: "

        for _ in range(15):
            spin_sequence = spin_sequence[-1:] + spin_sequence[:-1]  
            spin_text = " ".join(spin_sequence)
            embed = discord.Embed(
                title="Spinning the Case...",
                description=f"{black_square * 5} {pointer} {black_square * 5}\n {spin_text}\n{black_square * 5} {pointe2} {black_square * 5}",
                color=0x2F3136
            )
            await message.edit(embed=embed)
            await asyncio.sleep(0.2)


        middle_emote = spin_sequence[5] 
        spin_text = " ".join(spin_sequence)
        marked_spin_text = f"{black_square * 5} {pointer} {black_square * 5}\n {spin_text}\n{black_square * 5} {pointe2} {black_square * 5}"

        await self.finalize_open(interaction, message, marked_spin_text, middle_emote)

    async def finalize_open(self, interaction: discord.Interaction, message, marked_spin_text, middle_emote):
        rewards = {
            "🍎": 75,
            "🍌": 175,
            "🍇": 350,
            "🍉": 1250,
            "🍍": 2500,
            "🍈": 13000  
        }

        prize = rewards[middle_emote]

        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT chips FROM users WHERE user_id = ?', (interaction.user.id,))
        result = cursor.fetchone()
        current_chips = result[0]

        new_chips = current_chips - 250 + prize
        cursor.execute('UPDATE users SET chips = ? WHERE user_id = ?', (new_chips, interaction.user.id))

        conn.commit()
        conn.close()

        result_embed = discord.Embed(
            title="Case Result",
            description=f"{marked_spin_text}\n\n"
                        f"**You won {prize} chips!**\nYour new balance is {new_chips} <:chips4:1278671577105436724>. ",
            color=0x2F3136 if prize < 250 else 0x2F3136
        )

        await message.edit(embed=result_embed)

        await asyncio.sleep(6)
        await message.delete()

    @discord.app_commands.command(name="opencase", description="Open a case and win chips!")
    async def opencase(self, interaction: discord.Interaction):
        await self.open_case(interaction)

async def setup(bot):
    await bot.add_cog(CaseGame(bot))
