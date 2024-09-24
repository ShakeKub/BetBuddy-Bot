import discord
from discord.ext import commands
import random
from discord.ui import Button, View
import sqlite3

class Roulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    async def play_roulette(self, interaction: discord.Interaction, message=None):
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

        chip_emoji = self.get_chip_emoji(current_chips)
        bet_embed = discord.Embed(title="Place Your Bet", description=f"Your current chips: {current_chips} {chip_emoji}", color=0x3498db)
        bet_embed.add_field(name="Bet Amount", value="Choose the amount you want to bet:", inline=False)
        bet_embed.set_image(url="attachment://roulette.png") 

        view = View(timeout=None)
        range_buttons = [
            Button(label="1-25", style=discord.ButtonStyle.primary, custom_id="range_1_25", emoji="<:chips2:1278671592444133498>"),
            Button(label="25-100", style=discord.ButtonStyle.primary, custom_id="range_25_100", emoji="<:chips3:1278665072503160944>"),
            Button(label="100-1000", style=discord.ButtonStyle.primary, custom_id="range_100_1000", emoji="<:chips4:1278671577105436724>"),
            Button(label="All In", style=discord.ButtonStyle.secondary, custom_id="range_all_in", emoji="<:chips5:1278671563201445952>")
        ]
        for button in range_buttons:
            view.add_item(button)

        if message is None:
            await interaction.response.send_message(embed=bet_embed, view=view)
            message = await interaction.original_response()
        else:
            await message.edit(embed=bet_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            if inter.data['custom_id'].startswith("range_"):
                range_id = inter.data['custom_id'].split("_")[1:]
                await self.show_bet_amounts(interaction, message, range_id, current_chips)
            else:
                await message.delete()

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def show_bet_amounts(self, interaction: discord.Interaction, message, range_id, current_chips):
        bet_range, step = {
            '1_25': (25, 5),
            '25_100': (100, 5),
            '100_1000': (1000, 100)
        }.get("_".join(range_id), (current_chips, current_chips))

        if "_".join(range_id) == '25_100':
            bet_amounts = list(range(25, bet_range + 1, step)) + ([current_chips] if range_id[-1] == 'all_in' else [])
        elif "_".join(range_id) == '100_1000':
            bet_amounts = list(range(100, bet_range + 1, step)) + ([current_chips] if range_id[-1] == 'all_in' else [])
        else:
            bet_amounts = list(range(5, bet_range + 1, step)) + ([current_chips] if range_id[-1] == 'all_in' else [])

        bet_amounts_buttons = [Button(label=str(amount), style=discord.ButtonStyle.primary, custom_id=f"bet_{amount}") for amount in bet_amounts]

        bet_amounts_embed = discord.Embed(title="Choose Your Bet Amount", description="Select the amount you want to bet:", color=0x3498db)

        view = View(timeout=None)
        for button in bet_amounts_buttons:
            view.add_item(button)

        await message.edit(embed=bet_amounts_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            bet_amount = int(inter.data['custom_id'].split("_")[1])
            if bet_amount > current_chips:
                await inter.response.send_message("You don't have enough chips for this bet.")
                return

            await self.choose_bet_type(interaction, message, bet_amount)

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def choose_bet_type(self, interaction: discord.Interaction, message, bet_amount):
        bet_type_embed = discord.Embed(title="Choose Your Bet Type", description="Select the type of bet:", color=0x3498db)

        view = View(timeout=None)
        color_button = Button(label="Red/Black", style=discord.ButtonStyle.secondary, custom_id="color")
        parity_button = Button(label="Odd/Even", style=discord.ButtonStyle.primary, custom_id="parity")
        line_button = Button(label="Line Bet", style=discord.ButtonStyle.success, custom_id="line")
        view.add_item(color_button)
        view.add_item(parity_button)
        view.add_item(line_button)

        if message is None:
            await interaction.response.send_message(embed=bet_type_embed, view=view)
            message = await interaction.original_response()
        else:
            await message.edit(embed=bet_type_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            if inter.data['custom_id'] == "color":
                await self.choose_color(interaction, message, bet_amount)
            elif inter.data['custom_id'] == "parity":
                await self.choose_parity(interaction, message, bet_amount)
            elif inter.data['custom_id'] == "line":
                await self.choose_line(interaction, message, bet_amount)
            else:
                await message.delete()
                return

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def choose_color(self, interaction: discord.Interaction, message, bet_amount):
        color_embed = discord.Embed(title="Choose Your Color", description="Red or Black?", color=0x3498db)

        view = View(timeout=None)
        red_button = Button(label="Red", style=discord.ButtonStyle.danger, custom_id="red")
        black_button = Button(label="Black", style=discord.ButtonStyle.secondary, custom_id="black")
        view.add_item(red_button)
        view.add_item(black_button)

        if message is None:
            await interaction.response.send_message(embed=color_embed, view=view)
            message = await interaction.original_response()
        else:
            await message.edit(embed=color_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            chosen_color = inter.data['custom_id']
            await self.play_roulette_game(interaction, message, bet_amount, "color", chosen_color)

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def choose_parity(self, interaction: discord.Interaction, message, bet_amount):
        parity_embed = discord.Embed(title="Choose Your Parity", description="Odd or Even?", color=0x3498db)

        view = View(timeout=None)
        odd_button = Button(label="Odd", style=discord.ButtonStyle.primary, custom_id="odd")
        even_button = Button(label="Even", style=discord.ButtonStyle.primary, custom_id="even")
        view.add_item(odd_button)
        view.add_item(even_button)

        if message is None:
            await interaction.response.send_message(embed=parity_embed, view=view)
            message = await interaction.original_response()
        else:
            await message.edit(embed=parity_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            chosen_parity = inter.data['custom_id']
            await self.play_roulette_game(interaction, message, bet_amount, "parity", chosen_parity)

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def choose_line(self, interaction: discord.Interaction, message, bet_amount):
        line_embed = discord.Embed(title="Choose Your Line Bet", description="Select a line to bet on:", color=0x3498db)

        view = View(timeout=None)
        line_1_to_18_button = Button(label="1-18", style=discord.ButtonStyle.secondary, custom_id="line_1_18")
        line_19_to_36_button = Button(label="19-36", style=discord.ButtonStyle.secondary, custom_id="line_19_36")
        view.add_item(line_1_to_18_button)
        view.add_item(line_19_to_36_button)

        if message is None:
            await interaction.response.send_message(embed=line_embed, view=view)
            message = await interaction.original_response()
        else:
            await message.edit(embed=line_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            chosen_line = inter.data['custom_id']
            await self.play_roulette_game(interaction, message, bet_amount, "line", chosen_line)

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def play_roulette_game(self, interaction: discord.Interaction, message, bet_amount, bet_type, bet_value):
        result_number = random.randint(0, 36)  
        result_color = "red" if result_number % 2 == 0 else "black" 
        result_parity = "even" if result_number % 2 == 0 else "odd"  
        result_line = "line_1_18" if result_number <= 18 else "line_19_36"  

        if bet_type == "color":
            if bet_value == result_color:
                result = f"Congratulations! The color is {result_color}. You win {bet_amount} chips!"
                embed_color = 0x90ee90
                chip_change = bet_amount
            else:
                result = f"The color was {result_color}. You lose {bet_amount} chips."
                embed_color = 0xff0000
                chip_change = -bet_amount
        elif bet_type == "parity":
            if bet_value == result_parity:
                result = f"Congratulations! The number is {result_parity}. You win {bet_amount} chips!"
                embed_color = 0x90ee90
                chip_change = bet_amount
            else:
                result = f"The number was {result_parity}. You lose {bet_amount} chips."
                embed_color = 0xff0000
                chip_change = -bet_amount
        elif bet_type == "line":
            if bet_value == result_line:
                result = f"Congratulations! The number is in {result_line.replace('_', ' ')}. You win {bet_amount} chips!"
                embed_color = 0x90ee90
                chip_change = bet_amount
            else:
                result = f"The number was in {result_line.replace('_', ' ')}. You lose {bet_amount} chips."
                embed_color = 0xff0000
                chip_change = -bet_amount
        else:
            result = f"You guessed {result_number}. You lose {bet_amount} chips."
            embed_color = 0xff0000
            chip_change = -bet_amount

        embed = discord.Embed(title="Roulette", description="Spin Result!", color=embed_color)
        embed.add_field(name="Result", value=result, inline=False)

        replay_button = Button(label="Play Again", style=discord.ButtonStyle.primary, custom_id="replay")
        quit_button = Button(label="Quit", style=discord.ButtonStyle.danger, custom_id="quit")

        final_view = View()
        final_view.add_item(replay_button)
        final_view.add_item(quit_button)

        await message.edit(embed=embed, view=final_view)

        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET chips = chips + ?, xp = xp + 2 WHERE user_id = ?', (chip_change, interaction.user.id))
        conn.commit()
        conn.close()

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            if inter.data['custom_id'] == "replay":
                await self.play_roulette(interaction, message=message)

            elif inter.data['custom_id'] == "quit":
                await message.delete()

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    @discord.app_commands.command(name="roulette", description="Play a game of Roulette!")
    async def roulette(self, interaction: discord.Interaction):
        start_cog = self.bot.get_cog('Start')
        
        user_exists = await start_cog.check_for_user(interaction)
        if user_exists:
            await self.play_roulette(interaction)
        else:
            await start_cog.show_menu(interaction)

async def setup(bot):
    await bot.add_cog(Roulette(bot))
