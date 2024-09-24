import discord
from discord.ext import commands
from discord.ui import Button, View
import sqlite3
import random

class Mines(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_database()
        self.multipliers = self.generate_multipliers()
        self.games = {}  

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

    def generate_multipliers(self):
     
        multipliers = {}
        for mines in range(1, 16):
            base_multiplier = 1.5
            increment = 0.1 * mines 
            multipliers[mines] = base_multiplier + increment
        return multipliers

    async def update_user_xp(self, user_id, xp_gain=2):
        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT xp FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            cursor.execute('INSERT INTO users (user_id, xp) VALUES (?, ?)', (user_id, xp_gain))
        else:
            xp = result[0]
            xp += xp_gain
            cursor.execute('UPDATE users SET xp = ? WHERE user_id = ?', (xp, user_id))
        
        conn.commit()
        conn.close()

    @discord.app_commands.command(name="mines", description="Play a Mines-style game!")
    async def mines(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT chips FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result is None:
            await interaction.response.send_message("You are not registered. Please register first.", ephemeral=True)
            return

        current_chips = result[0]
        if current_chips < 10:
            await interaction.response.send_message("You need at least 10 chips to play.", ephemeral=True)
            return

        await interaction.response.send_message(embed=self.create_bet_embed(current_chips), view=self.create_bet_view(current_chips), ephemeral=True)

    def create_bet_embed(self, current_chips):
        embed = discord.Embed(
            title="💣 Mines Game - Place Your Bet",
            description=f"You have **{current_chips}** chips.\n\nSelect your bet amount:",
            color=0xFFD700
        )
        return embed

    def create_bet_view(self, current_chips):
        view = View(timeout=60)
        bet_values = [10, 50, 100, 500, 1000, 5000]
        for bet in bet_values:
            if bet <= current_chips:
                button = Button(label=f"{bet} Chips", style=discord.ButtonStyle.primary, custom_id=f"bet_{bet}")
                view.add_item(button)
        all_in_button = Button(label="All In", style=discord.ButtonStyle.danger, custom_id=f"bet_{current_chips}")
        view.add_item(all_in_button)
        view.on_timeout = lambda: view.clear_items()
        return view

    def create_mines_embed(self, bet_amount):
        embed = discord.Embed(
            title="💣 Mines Game - Select Mines",
            description=f"Your bet: **{bet_amount}** chips.\n\nSelect the number of mines (1-15):",
            color=0xFFD700
        )
        return embed

    def create_mines_view(self):
        view = View(timeout=60)
        for i in range(1, 16):
            button = Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"mines_{i}")
            view.add_item(button)
        view.on_timeout = lambda: view.clear_items()
        return view

    def create_game_embed(self, bet_amount, mine_count, revealed_tiles, potential_winnings):
        embed = discord.Embed(
            title="💣 Mines Game",
            description=(
                f"**Bet Amount:** {bet_amount} chips\n"
                f"**Mines:** {mine_count}\n"
                f"**Revealed Tiles:** {len(revealed_tiles)}\n"
                f"**Potential Winnings:** {potential_winnings} chips\n\n"
                "Click on the buttons to reveal safe tiles.\n"
                "Click **Cash Out** to collect your winnings anytime."
            ),
            color=0x00FF00
        )
        return embed

    def create_game_view(self, minefield, revealed_tiles, show_quit_button=False):
        view = View(timeout=120)
        for i in range(20):
            if i in revealed_tiles:
                if minefield[i]:
                    button = Button(label="💣", style=discord.ButtonStyle.danger, disabled=True)
                else:
                    button = Button(label="💎", style=discord.ButtonStyle.success, disabled=True)
            else:
                button = Button(label="‎ ", style=discord.ButtonStyle.secondary, custom_id=f"tile_{i}")
            view.add_item(button)
        
        cashout_button = Button(label="💰 Cash Out", style=discord.ButtonStyle.primary, custom_id="cashout")
        view.add_item(cashout_button)

        if show_quit_button:
            quit_button = Button(label="🚪 Quit", style=discord.ButtonStyle.danger, custom_id="quit")
            view.add_item(quit_button)

        view.on_timeout = lambda: view.clear_items()
        return view

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.data and 'custom_id' in interaction.data:
            custom_id = interaction.data['custom_id']
            if custom_id.startswith("bet_"):
                if interaction.user.id not in self.games:
                    await interaction.response.send_message("This game is not active or has expired.", ephemeral=True)
                    return False
        return True

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.data or 'custom_id' not in interaction.data:
            return

        custom_id = interaction.data['custom_id']

        if custom_id.startswith("bet_"):
            await self.handle_bet_selection(interaction, custom_id)
        elif custom_id.startswith("mines_"):
            await self.handle_mine_selection(interaction, custom_id)
        elif custom_id.startswith("tile_") or custom_id == "cashout":
            await self.handle_gameplay(interaction, custom_id)
        elif custom_id == "quit":
            await self.handle_quit(interaction)

    async def handle_bet_selection(self, interaction, custom_id):
        bet_amount = int(custom_id.split('_')[1])
        user_id = interaction.user.id

        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT chips FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()

        current_chips = result[0]

        if bet_amount > current_chips:
            await interaction.response.send_message("You don't have enough chips for that bet.", ephemeral=True)
            return

        embed = self.create_mines_embed(bet_amount)
        view = self.create_mines_view()

      
        self.games[user_id] = {
            'bet_amount': bet_amount,
            'game_state': 'bet'
        }

        await interaction.response.edit_message(embed=embed, view=view)

    async def handle_mine_selection(self, interaction, custom_id):
        mine_count = int(custom_id.split('_')[1])
        bet_amount = self.games[interaction.user.id]['bet_amount']
        user_id = interaction.user.id

      
        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET chips = chips - ? WHERE user_id = ?', (bet_amount, user_id))
        conn.commit()
        conn.close()

       
        mine_positions = random.sample(range(20), mine_count)
        minefield = [False] * 20
        for pos in mine_positions:
            minefield[pos] = True

        revealed_tiles = []
        potential_winnings = bet_amount 

        embed = self.create_game_embed(bet_amount, mine_count, revealed_tiles, potential_winnings)
        view = self.create_game_view(minefield, revealed_tiles)

       
        self.games[user_id].update({
            'minefield': minefield,
            'revealed_tiles': revealed_tiles,
            'mine_count': mine_count,
            'potential_winnings': potential_winnings,
            'game_state': 'playing'
        })

        await interaction.response.edit_message(embed=embed, view=view)

    async def handle_gameplay(self, interaction, custom_id):
        user_id = interaction.user.id
        game_state = self.games.get(user_id)

        if not game_state:
            await interaction.response.send_message("This game is not active or has expired.", ephemeral=True)
            return

        if game_state['game_state'] != 'playing':
            await interaction.response.send_message("The game is not active at the moment.", ephemeral=True)
            return

        minefield = game_state['minefield']
        revealed_tiles = game_state['revealed_tiles']
        bet_amount = game_state['bet_amount']
        mine_count = game_state['mine_count']

        if custom_id == "cashout":
            winnings = game_state['potential_winnings']
            conn = sqlite3.connect('discord_database.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET chips = chips + ? WHERE user_id = ?', (winnings, user_id))
            conn.commit()
            conn.close()

            await self.update_user_xp(user_id, xp_gain=5)

            embed = discord.Embed(
                title="💰 Cash Out Successful!",
                description=f"You cashed out and won **{winnings}** chips!",
                color=0x00FF00
            )
            view = self.create_game_view(minefield, revealed_tiles, show_quit_button=True)
            await interaction.response.edit_message(embed=embed, view=view)
            return

        if custom_id == "quit":
            embed = discord.Embed(
                title="🚪 Game Over",
                description="You have quit the game.",
                color=0xFF0000
            )
            view = View()
            del self.games[user_id]
            await interaction.response.edit_message(embed=embed, view=view)
            return

        tile_index = int(custom_id.split('_')[1])

        if tile_index in revealed_tiles:
            await interaction.response.defer()
            return

        revealed_tiles.append(tile_index)

        if minefield[tile_index]:
            embed = discord.Embed(
                title="💥 Boom! You hit a mine.",
                description=f"You lost your bet of **{bet_amount}** chips.",
                color=0xFF0000
            )
            for i in range(20):
                if minefield[i] and i not in revealed_tiles:
                    revealed_tiles.append(i)
            view = self.create_game_view(minefield, revealed_tiles, show_quit_button=True)
            await interaction.response.edit_message(embed=embed, view=view)
            del self.games[user_id]
        else:
            revealed_count = len(revealed_tiles)
            safe_tiles = 20 - mine_count
            if revealed_count < safe_tiles:
                multiplier = self.multipliers[mine_count]
                percentage_multiplier = (revealed_count / safe_tiles) * multiplier
                potential_winnings = round(bet_amount * percentage_multiplier)
                
                game_state['potential_winnings'] = potential_winnings
                embed = self.create_game_embed(bet_amount, mine_count, revealed_tiles, potential_winnings)
                view = self.create_game_view(minefield, revealed_tiles)

                if revealed_count == safe_tiles:
                    conn = sqlite3.connect('discord_database.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE users SET chips = chips + ? WHERE user_id = ?', (potential_winnings, user_id))
                    conn.commit()
                    conn.close()

                    await self.update_user_xp(user_id, xp_gain=10)

                    embed = discord.Embed(
                        title="🎉 Congratulations! You cleared the board!",
                        description=f"You won **{potential_winnings}** chips!",
                        color=0x00FF00
                    )
                    view = self.create_game_view(minefield, revealed_tiles, show_quit_button=True)
                    del self.games[user_id]
                else:
                    await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.response.edit_message(embed=embed, view=view)

    async def handle_quit(self, interaction):
        user_id = interaction.user.id
        if user_id in self.games:
            del self.games[user_id]

        embed = discord.Embed(
            title="🚪 Game Over",
            description="You have quit the game.",
            color=0xFF0000
        )
        view = View()
        await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Mines(bot))
