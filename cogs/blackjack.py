import discord
from discord.ext import commands
import random
from discord.ui import Button, View
import sqlite3

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.card_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
            'J': 10, 'Q': 10, 'K': 10, 'A': 11
        }
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

    async def update_user_xp(self, user_id):
        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT xp FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute('INSERT INTO users (user_id, xp) VALUES (?, ?)', (user_id, 2))
        else:
            xp = result[0]
            xp += 2
            cursor.execute('UPDATE users SET xp = ? WHERE user_id = ?', (xp, user_id))
        
        conn.commit()
        conn.close()

    async def play_blackjack(self, interaction: discord.Interaction, message=None):
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

    async def choose_bet_amount(self, interaction: discord.Interaction, message=None, selected_range=None):
        user_id = interaction.user.id
        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT chips FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()

        current_chips = result[0]

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

            def check(inter):
                return inter.user.id == interaction.user.id and inter.message.id == message.id

            try:
                inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
                await inter.response.defer()

                bet_amount = int(inter.data['custom_id'].split('_')[1])
                if bet_amount > current_chips:
                    await message.delete()
                    return

                await self.play_game(interaction, message, bet_amount, bet_amount == current_chips)

            except Exception as e:
                print(f"Interaction failed with error: {e}")
                await message.delete()

    async def play_game(self, interaction: discord.Interaction, message, bet_amount, all_in):
        casino_hand = [random.choice(list(self.card_values.keys())), random.choice(list(self.card_values.keys()))]
        player_hand = [random.choice(list(self.card_values.keys())), random.choice(list(self.card_values.keys()))]

        casino_total = sum([self.card_values[card] for card in casino_hand])
        player_total = sum([self.card_values[card] for card in player_hand])

        embed = discord.Embed(title="Blackjack", description="Let's play Blackjack!", color=0x3498db)  
        embed.add_field(
            name="Casino's Hand", 
            value=f"**{casino_hand[0]}** and ?\n(Total: **{casino_total - self.card_values[casino_hand[1]]}**)", 
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)  
        embed.add_field(
            name="Your Hand", 
            value=f"**{'** and **'.join(player_hand)}**\n(Total: **{player_total}**)", 
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=False)  
        embed.set_footer(text="Choose your action using the buttons below.")
        embed.set_image(url="attachment://blackjack.png")  

        view = View(timeout=None)  
        hit_button = Button(label="Hit", style=discord.ButtonStyle.primary, custom_id="hit")
        stay_button = Button(label="Stay", style=discord.ButtonStyle.primary, custom_id="stay")

        if not all_in:
            double_button = Button(label="Double", style=discord.ButtonStyle.primary, custom_id="double")
            view.add_item(double_button)
        view.add_item(hit_button)
        view.add_item(stay_button)

        if message is None:
            await interaction.response.send_message(embed=embed, view=view)
            message = await interaction.original_response()
        else:
            await message.edit(embed=embed, view=view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        while player_total < 21:
            try:
                inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)

                if inter.data['custom_id'] == "hit":
                    new_card = random.choice(list(self.card_values.keys()))
                    player_hand.append(new_card)
                    player_total += self.card_values[new_card]
                    embed.set_field_at(
                        2, 
                        name="Your Hand", 
                        value=f"**{'** and **'.join(player_hand)}**\n(Total: **{player_total}**)", 
                        inline=True
                    )
                    await inter.response.edit_message(embed=embed, view=view)  

                elif inter.data['custom_id'] == "stay":
                    await inter.response.defer()  
                    break

                elif inter.data['custom_id'] == "double":
                    new_card = random.choice(list(self.card_values.keys()))
                    player_hand.append(new_card)
                    player_total += self.card_values[new_card]
                    bet_amount *= 2  
                    embed.set_field_at(
                        2, 
                        name="Your Hand", 
                        value=f"**{'** and **'.join(player_hand)}**\n(Total: **{player_total}**)", 
                        inline=True
                    )
                    await inter.response.edit_message(embed=embed, view=view)
                    break

            except Exception as e:
                print(f"Interaction failed with error: {e}")
                await message.delete()
                return  

        while casino_total < 17:
            new_card = random.choice(list(self.card_values.keys()))
            casino_hand.append(new_card)
            casino_total += self.card_values[new_card]

        result = ""
        embed.color = 0x3498db 

        if player_total > 21:
            result = "You busted! Casino wins."
            embed.color = 0xff0000  

            conn = sqlite3.connect('discord_database.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET chips = chips - ? WHERE user_id = ?', (bet_amount, interaction.user.id))
            conn.commit()
            conn.close()
        elif casino_total > 21 or player_total > casino_total:
            result = "Congratulations! You win!"
            embed.color = 0x90ee90  

            conn = sqlite3.connect('discord_database.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET chips = chips + ? WHERE user_id = ?', (bet_amount, interaction.user.id))
            conn.commit()
            conn.close()
        elif player_total == casino_total:
            result = "It's a tie!"
            embed.color = 0xffa500  
        else:
            result = "Casino wins. Better luck next time."
            embed.color = 0xff0000  

            conn = sqlite3.connect('discord_database.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET chips = chips - ? WHERE user_id = ?', (bet_amount, interaction.user.id))
            conn.commit()
            conn.close()

        embed.add_field(
            name="Casino's Final Hand", 
            value=f"**{'** and **'.join(casino_hand)}**\n(Total: **{casino_total}**)", 
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True)  
        embed.add_field(name="Result", value=result, inline=True)

   
        await self.update_user_xp(interaction.user.id)

        replay_button = Button(label="Play Again", style=discord.ButtonStyle.primary, custom_id="replay")
        quit_button = Button(label="Quit", style=discord.ButtonStyle.danger, custom_id="quit")

        final_view = View()
        final_view.add_item(replay_button)
        final_view.add_item(quit_button)

        await message.edit(embed=embed, view=final_view)

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)

            if inter.data['custom_id'] == "replay":
                await self.play_blackjack(inter, message=message)  

            elif inter.data['custom_id'] == "quit":
                await message.delete()  

        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()
            return 

    @discord.app_commands.command(name="blackjack", description="Play a game of Blackjack!")
    async def blackjack(self, interaction: discord.Interaction):
        start_cog = self.bot.get_cog('Start')
        
        user_exists = await start_cog.check_for_user(interaction)
        if user_exists:
            await self.play_blackjack(interaction)
        else:
            await start_cog.show_menu(interaction) 

async def setup(bot):
    await bot.add_cog(Blackjack(bot))
