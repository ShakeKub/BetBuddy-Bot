import discord
from discord.ext import commands
import random
from discord.ui import Button, View
import sqlite3

class DiceGame(commands.Cog):
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

    def get_chip_emoji(self, chips):
        """Returns the emoji for the given number of chips."""
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

    async def choose_bet_amount(self, interaction: discord.Interaction, bet_amount: int):
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

        if current_chips <= 0:
            await interaction.response.send_message("You do not have enough chips to place a bet. Please earn or deposit more chips.")
            return

        if bet_amount > current_chips:
            await interaction.response.send_message(f"You do not have enough chips to bet {bet_amount}. You currently have {current_chips} chips.")
            return

        await self.choose_dice_range(interaction, bet_amount)

    async def choose_dice_range(self, interaction: discord.Interaction, bet_amount: int):
        dice_embed = discord.Embed(
            title="Choose Dice Range",
            description="Select the range of dice you want to bet on. <:dice:1278709560600956980>",
            color=0x2F3136
        )

        view = View(timeout=None)
        range_1_6_button = Button(label="1-6", style=discord.ButtonStyle.primary, custom_id="range_1_6")
        range_1_12_button = Button(label="1-12", style=discord.ButtonStyle.primary, custom_id="range_1_12")
        view.add_item(range_1_6_button)
        view.add_item(range_1_12_button)

        await interaction.response.send_message(embed=dice_embed, view=view)
        message = await interaction.original_response()

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()

            if inter.data['custom_id'] == "range_1_6":
                dice_range = 6
            elif inter.data['custom_id'] == "range_1_12":
                dice_range = 12
            else:
                await inter.message.delete()
                return

            await self.choose_number(interaction, bet_amount, dice_range)

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def choose_number(self, interaction: discord.Interaction, bet_amount: int, dice_range: int):
        number_embed = discord.Embed(
            title="Choose a Number to Bet On",
            description=f"Bet on a number between 1 and {dice_range}. <:dice:1278709560600956980>",
            color=0x3498db
        )

        view = View(timeout=None)
        for i in range(1, dice_range + 1):
            number_button = Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"number_{i}")
            view.add_item(number_button)

        message = interaction.message or await interaction.original_response()

        await message.edit(embed=number_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()

            chosen_number = int(inter.data['custom_id'].split('_')[1])

            await self.roll_dice(interaction, chosen_number, bet_amount, dice_range)

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def roll_dice(self, interaction: discord.Interaction, chosen_number: int, bet_amount: int, dice_range: int):
        roll_result = random.randint(1, dice_range)
        win_amount = 0

        if roll_result == chosen_number:
            if dice_range == 6:
                win_amount = bet_amount * 6
            elif dice_range == 12:
                win_amount = bet_amount * 12
        else:
            win_amount = -bet_amount

        result_message = f"The roll result is {roll_result}! <:dice:1278709560600956980>"
        if win_amount > 0:
            result_message += f"\nCongratulations! You won {win_amount} chips!"
        else:
            result_message += "\nYou lost this round. Better luck next time!"

        embed = discord.Embed(
            title="Roll Result",
            description=result_message,
            color=0x2F3136
        )
        if win_amount > 0:
            embed.color = 0x90ee90
        else:
            embed.color = 0xff0000

        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT chips, xp FROM users WHERE user_id = ?', (interaction.user.id,))
        result = cursor.fetchone()
        if result:
            current_chips, current_xp = result
        else:
            current_chips = 0
            current_xp = 0

        cursor.execute('UPDATE users SET chips = chips + ? WHERE user_id = ?', (win_amount, interaction.user.id))
        cursor.execute('UPDATE users SET xp = xp + 2 WHERE user_id = ?', (interaction.user.id,))

        conn.commit()
        conn.close()

        quit_button = Button(label="Quit", style=discord.ButtonStyle.danger, custom_id="quit")

        final_view = View()
        final_view.add_item(quit_button)

        message = interaction.message or await interaction.original_response()

        await message.edit(embed=embed, view=final_view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()

            if inter.data['custom_id'] == "replay":
                await self.choose_bet_amount(interaction, bet_amount)
            elif inter.data['custom_id'] == "quit":
                await message.delete()
        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    @discord.app_commands.command(name="dice", description="Play a dice game!")
    async def dice(self, interaction: discord.Interaction, chips: int):
        start_cog = self.bot.get_cog('Start')

        user_exists = await start_cog.check_for_user(interaction)
        if user_exists:
            await self.choose_bet_amount(interaction, chips)
        else:
            await start_cog.show_menu(interaction)

async def setup(bot):
    await bot.add_cog(DiceGame(bot))
