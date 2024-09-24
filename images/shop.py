import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import asyncio

class ShopSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_PATH = r"C:\Users\Fatek\Documents\GitHub\BetBuddy\discord_database.db"
        self.setup_database()

  
        self.shop_items = {
            'cap': {
                'name': 'Cool Cap',
                'emoji': '<:cap:1279523119719120998>',
                'price': 5000,
                'description': 'A stylish cap to show off your swag!'
            },
            'glasses': {
                'name': 'Sunglasses',
                'emoji': '<:glasses:1279523101914431669>',
                'price': 5000,
                'description': 'Shades that make you look cooler than the sun.'
            },
            'cigar': {
                'name': 'Luxury Cigar',
                'emoji': '<:cigar:1279523089633513472>',
                'price': 5000,
                'description': 'For those who appreciate the finer things in life.'
            }
        }

    def setup_database(self):
        """Ensure the 'items' column exists in the users table."""
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
             
                cursor.execute("""
                    ALTER TABLE users ADD COLUMN items TEXT DEFAULT ''
                """)
        except sqlite3.OperationalError:
         
            pass
        except sqlite3.Error as e:
            print(f"Database error during setup: {e}")

    def get_user_data(self, user_id):
        """Retrieve user data from the database."""
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT chips, level, items FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                return result if result else None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

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

    async def create_user(self, user_id):
        """Create a new user profile in the database."""
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (user_id, chips, xp, level, items) VALUES (?, ?, ?, ?, ?)', (user_id, 250, 0, 1, ''))
                conn.commit()

            embed_msg = discord.Embed(
                title='Welcome to BetBuddy 🍒🃏',
                color=discord.Color.magenta(),
                description=(
                    'Congratulations on creating your new account! 🎉\n\n'
                    'Remember to play responsibly and know your limits.\n\n'
                    '**Commands to get you started:**\n'
                    '• **/slots** - Try your luck with our machines! <:slots:1278993029801185330>\n'
                    '• **/blackjack** - Test your skills in a game of Blackjack <:card_clubs:1278709601382039674>\n'
                    '• **/roulette** - Spin the wheel and see where it lands <:roulette:1278998129064284211>\n'
                    '• **/stats** - Check your gaming stats and progress\n'
                    '• **/daily** - Claim your daily rewards\n'
                    '• **/leaderboard** - See how you stack up against other players\n'
                    '• **/help** - Get a list of all available commands and assistance.\n\n'
                    '*Have fun and good luck! 🍀*'
                )
            )
            return embed_msg
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return discord.Embed(title='Error', description='There was an error creating your profile.', color=discord.Color.red())

    async def update_user_items(self, user_id, item_key):
        """Add purchased item to the user's inventory."""
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT items FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if result is None:
                    return False

                current_items = result[0]
                updated_items = current_items + ',' + item_key if current_items else item_key
                cursor.execute("UPDATE users SET items = ? WHERE user_id = ?", (updated_items, user_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    async def update_user_chips(self, user_id, amount):
        """Deduct chips from the user's balance."""
        try:
            with sqlite3.connect(self.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT chips FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if result is None:
                    return False, 0

                current_chips = result[0]
                if current_chips < amount:
                    return False, current_chips

                new_balance = current_chips - amount
                cursor.execute("UPDATE users SET chips = ? WHERE user_id = ?", (new_balance, user_id))
                conn.commit()
                return True, new_balance
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False, 0

    @app_commands.command(name='shop', description='Browse and purchase items from the shop.')
    async def shop(self, interaction: discord.Interaction):
        user = interaction.user
        user_data = self.get_user_data(user.id)

        if user_data is None:

            create_profile_embed = discord.Embed(
                title="Create Your Profile!",
                description="It looks like you don't have a profile yet. Please create one to access the shop.",
                color=discord.Color.red()
            )
            create_profile_embed.add_field(
                name="To create a profile:",
                value="Click the button below to create your profile and get started!",
                inline=False
            )
            view = CreateAccountView(self)
            await interaction.response.send_message(embed=create_profile_embed, view=view, ephemeral=True)
            return

        chips, level, items = user_data
        chip_emoji = self.get_chip_emoji(chips)

        if level < 5:

            embed = discord.Embed(
                title="Access Denied",
                description="You need to be at least **Level 5** to access the shop. Keep playing to level up!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="🛒 Welcome to the Shop!",
            description="Browse and purchase exclusive items using your chips.",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.add_field(name="Your Chips", value=f"{chips} {chip_emoji}", inline=False)

        for item_key, item_info in self.shop_items.items():
            embed.add_field(
                name=f"{item_info['emoji']} {item_info['name']} - {item_info['price']} Chips",
                value=item_info['description'],
                inline=False
            )

        view = ShopView(self, user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ShopView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=120)  
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label='Buy Cap', style=discord.ButtonStyle.secondary, emoji='<:cap:1279523119719120998>')
    async def buy_cap(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_purchase(interaction, 'cap')

    @discord.ui.button(label='Buy Glasses', style=discord.ButtonStyle.secondary, emoji='<:glasses:1279523101914431669>')
    async def buy_glasses(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_purchase(interaction, 'glasses')

    @discord.ui.button(label='Buy Cigar', style=discord.ButtonStyle.secondary, emoji='<:cigar:1279523089633513472>')
    async def buy_cigar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_purchase(interaction, 'cigar')

    async def handle_purchase(self, interaction, item_key):

        user = interaction.user
        item = self.cog.shop_items[item_key]


        user_data = self.cog.get_user_data(self.user_id)
        if user_data and item_key in user_data[2].split(','):
            embed = discord.Embed(
                title="Purchase Failed",
                description=f"You already own **{item['name']}**.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

        success, new_balance = await self.cog.update_user_chips(self.user_id, item['price'])

        if success:
            await self.cog.update_user_items(self.user_id, item_key)
            embed = discord.Embed(
                title="Purchase Successful",
                description=f"You have successfully purchased **{item['name']}** for {item['price']} chips <:chips5:1278671563201445952> ! ",
                color=discord.Color.green()
            )
            embed.add_field(name="New Balance", value=f"{new_balance} {self.cog.get_chip_emoji(new_balance)}", inline=False)
        else:
            embed = discord.Embed(
                title="Purchase Failed",
                description=f"You don't have enough chips to buy **{item['name']}**.",
                color=discord.Color.red()
            )

        await interaction.response.edit_message(embed=embed, view=None)

class CreateAccountView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog

    @discord.ui.button(label="Create Account", style=discord.ButtonStyle.success)
    async def create_account(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self.cog.create_user(interaction.user.id)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ShopSystem(bot))
