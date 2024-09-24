import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import sqlite3
import time
import asyncio
import math

class HiLoGame(commands.Cog):
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
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                loss_streak INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def get_db_connection(self):
        return sqlite3.connect('discord_database.db')

    def execute_db_query(self, query, params=(), fetchone=False):
        while True:
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute(query, params)
                if fetchone:
                    result = cursor.fetchone()
                else:
                    conn.commit()
                    result = None
                conn.close()
                return result
            except sqlite3.OperationalError as e:
                if 'locked' in str(e):
                    time.sleep(0.1) 
                else:
                    raise

    async def update_user_stats(self, user_id, loss=False):
        user = self.execute_db_query('SELECT loss_streak FROM users WHERE user_id = ?', (user_id,), fetchone=True)
        if user is None:
            self.execute_db_query('INSERT INTO users (user_id, loss_streak) VALUES (?, ?)', (user_id, 1 if loss else 0))
            loss_streak = 1 if loss else 0
        else:
            loss_streak = user[0]
            if loss:
                loss_streak += 1
            else:
                loss_streak = 0
            if loss_streak == 3:
               
                pass
            self.execute_db_query('UPDATE users SET loss_streak = ? WHERE user_id = ?', (loss_streak, user_id))

    async def update_user_xp(self, user_id, xp_gain):
        user_data = self.execute_db_query('SELECT xp FROM users WHERE user_id = ?', (user_id,), fetchone=True)
        if user_data is None:
            self.execute_db_query('INSERT INTO users (user_id, xp) VALUES (?, ?)', (user_id, xp_gain))
            return

        current_xp = user_data[0]
        new_xp = current_xp + xp_gain
        xp_cap = 5000  

        if new_xp > xp_cap:
            new_xp = xp_cap

        self.execute_db_query('UPDATE users SET xp = ? WHERE user_id = ?', (new_xp, user_id))

    def get_xp_for_next_level(self, level):
        
        return 0

    async def choose_bet_amount(self, interaction: discord.Interaction, message=None, selected_range=None):
        user_id = interaction.user.id
        result = self.execute_db_query('SELECT chips FROM users WHERE user_id = ?', (user_id,), fetchone=True)

        if result is None:
            await interaction.response.send_message("You are not registered. Please register first.")
            return

        current_chips = result[0] or 0

        if current_chips <= 0:
            msg = await interaction.response.send_message("You don't have enough chips to play. Please get more chips or use the register command to start with some chips.")
            await asyncio.sleep(15)  
            await msg.delete()
            return

        if selected_range:
            min_bet, max_bet, increment = selected_range
            bet_embed = discord.Embed(
                title="Place Your Bet",
                description=f"Your current chips: {current_chips} {self.get_chip_emoji(current_chips)}",
                color=0x3498db
            )
            bet_embed.add_field(name="Bet Amount", value=f"Choose the amount you want to bet (from {min_bet} to {max_bet}):", inline=False)

            view = View(timeout=None)
            for amount in range(min_bet, max_bet + 1, increment):
                bet_button = Button(label=f"Bet {amount}", style=discord.ButtonStyle.primary, custom_id=f"bet_{amount}")
                view.add_item(bet_button)
            if min_bet < current_chips:
                all_in_button = Button(label="All In", style=discord.ButtonStyle.secondary, custom_id="bet_all_in")
                view.add_item(all_in_button)

            if message is None:
                await interaction.response.send_message(embed=bet_embed, view=view)
                message = await interaction.original_response()
            else:
                await message.edit(embed=bet_embed, view=view)

        else:
            range_embed = discord.Embed(
                title="Choose Betting Range",
                description=f"Your current chips: {current_chips} {self.get_chip_emoji(current_chips)}",
                color=0x3498db
            )
            range_embed.add_field(name="Betting Ranges", value="Select a betting range:", inline=False)

            view = View(timeout=None)
            range_1_25 = Button(label="1-25", style=discord.ButtonStyle.primary, custom_id="range_1_25", emoji="<:chips2:1278671592444133498>")
            range_25_100 = Button(label="25-100", style=discord.ButtonStyle.primary, custom_id="range_25_100", emoji="<:chips3:1278665072503160944>")
            range_100_1000 = Button(label="100-1000", style=discord.ButtonStyle.primary, custom_id="range_100_1000", emoji="<:chips4:1278671577105436724>")
            all_in = Button(label="All In", style=discord.ButtonStyle.secondary, custom_id="range_all_in", emoji="<:chips5:1278671563201445952>")

            view.add_item(range_1_25)
            view.add_item(range_25_100)
            view.add_item(range_100_1000)
            view.add_item(all_in)

            if message is None:
                await interaction.response.send_message(embed=range_embed, view=view)
                message = await interaction.original_response()
            else:
                await message.edit(embed=range_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            if selected_range:
                bet_amount = int(inter.data['custom_id'].split('_')[1])
                if bet_amount > current_chips:
                    await message.delete()
                    return

                await self.play_hi_lo(interaction, message, bet_amount)
            else:
                if inter.data['custom_id'] == "range_1_25":
                    await self.choose_bet_amount(interaction, message=message, selected_range=(5, 25, 5))
                elif inter.data['custom_id'] == "range_25_100":
                    await self.choose_bet_amount(interaction, message=message, selected_range=(25, 100, 5))
                elif inter.data['custom_id'] == "range_100_1000":
                    await self.choose_bet_amount(interaction, message=message, selected_range=(100, 1000, 100))
                elif inter.data['custom_id'] == "range_all_in":
                    await self.choose_bet_amount(interaction, message=message, selected_range=(current_chips, current_chips, 1))
                else:
                    await message.delete()

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    async def play_hi_lo(self, interaction: discord.Interaction, message, bet_amount):
        number = random.randint(1, 10)
        guess_embed = discord.Embed(
            title="Hi-Lo Game",
            description=f"Current number is {number}. Guess if the next number will be higher or lower.",
            color=0x3498db
        )
        guess_embed.add_field(name="Choices", value="Click the button to guess:", inline=False)

        higher_button = Button(label="Higher", style=discord.ButtonStyle.success, custom_id="higher")
        lower_button = Button(label="Lower", style=discord.ButtonStyle.danger, custom_id="lower")

        view = View()
        view.add_item(higher_button)
        view.add_item(lower_button)

        await message.edit(embed=guess_embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()  

            next_number = random.randint(1, 10)
            win = (inter.data['custom_id'] == "higher" and next_number > number) or \
                  (inter.data['custom_id'] == "lower" and next_number < number)
            if win:
                winnings = bet_amount * 0.25
                winnings_rounded = math.ceil(winnings) 
                result_embed = discord.Embed(
                    title="Hi-Lo Game",
                    description=f"The next number was {next_number}. You won {winnings_rounded} chips!",
                    color=0x90ee90
                )
           
                self.execute_db_query('UPDATE users SET chips = chips + ? WHERE user_id = ?', (winnings_rounded, interaction.user.id))
                await self.update_user_stats(interaction.user.id)
            else:
                result_embed = discord.Embed(
                    title="Hi-Lo Game",
                    description=f"The next number was {next_number}. You lost {bet_amount} chips.",
                    color=0xff0000
                )
              
                self.execute_db_query('UPDATE users SET chips = chips - ? WHERE user_id = ?', (bet_amount, interaction.user.id))
                await self.update_user_stats(interaction.user.id, loss=True)

            await self.update_user_xp(interaction.user.id, xp_gain=2)

            result_embed.add_field(name="Play Again", value="Would you like to play another round or quit?", inline=False)

            replay_button = Button(label="Play Again", style=discord.ButtonStyle.primary, custom_id="replay")
            quit_button = Button(label="Quit", style=discord.ButtonStyle.danger, custom_id="quit")

            final_view = View()
            final_view.add_item(replay_button)
            final_view.add_item(quit_button)

            await message.edit(embed=result_embed, view=final_view)

            def check(inter):
                return inter.user.id == interaction.user.id and inter.message.id == message.id

            try:
                inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
                await inter.response.defer()  

                if inter.data['custom_id'] == "replay":
                    result = self.execute_db_query('SELECT chips FROM users WHERE user_id = ?', (interaction.user.id,), fetchone=True)
                    current_chips = result[0] if result else 0

                    if current_chips <= 0:
                        await message.edit(embed=discord.Embed(
                            title="Insufficient Chips",
                            description="You don't have enough chips to play. Please get more chips or use the register command to start with some chips.",
                            color=0xff0000
                        ), view=None)
                        await asyncio.sleep(15) 
                        await message.delete()
                        return

                    await self.choose_bet_amount(interaction, message=message)
                elif inter.data['custom_id'] == "quit":
                    await message.delete()
            except Exception as e:
                print(f"Interaction failed with error: {e}")
                await message.delete()

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    def get_chip_emoji(self, chips):
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

    @discord.app_commands.command(name="hilo", description="Play a Hi-Lo game!")
    async def hilo(self, interaction: discord.Interaction):
        start_cog = self.bot.get_cog('Start')
        user_exists = await start_cog.check_for_user(interaction)
        if user_exists:
            await self.choose_bet_amount(interaction)
        else:
            await start_cog.show_menu(interaction)

async def setup(bot):
    await bot.add_cog(HiLoGame(bot))
