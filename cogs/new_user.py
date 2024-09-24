import discord
from discord.ext import commands
import sqlite3

class Start(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print('start.py is loaded')
        
    async def show_menu(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        has_account = await self.check_for_user(interaction)

        if has_account:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Profile Found',
                    description='You already have a profile.',
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        else:
            embed_msg = discord.Embed(
                title='Create a Profile',
                description='Welcome new player, if you wish to create a profile click the button below!',
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed_msg, view=StartButtons(self, user_id))
        
    async def check_for_user(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        connection = sqlite3.connect('./discord_database.db')
        cursor = connection.cursor()
        
        cursor.execute('SELECT * FROM Users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        connection.close()
        
        return result is not None
    
    async def create_user(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        connection = sqlite3.connect('./discord_database.db')
        cursor = connection.cursor()
        
        cursor.execute('INSERT INTO Users (user_id, chips, level, xp) VALUES (?, ?, ?, ?)',
                       (user_id, 250, 1, 0))
        connection.commit()
        connection.close()
        embed_msg = discord.Embed(title='Welcome to BetBuddy 🍒🃏',
                                  color=discord.Color.green())
        embed_msg.add_field(name='Congratulations on creating your new account! 🎉 Before you dive into the fun, please remember that gambling can be addictive. Play responsibly and know your limits.',
                            value='To get started, here are some commands you can use:\n\n**/slots ** - Try your luck with our machines! <:slots:1278993029801185330>\n**/blackjack ** - Test your skills in a game of Blackjack <:card_clubs:1278709601382039674>\n**/roulette ** - Spin the wheel and see where it lands <:roulette:1278998129064284211>\n**/stats ** - Check your gaming stats and progress\n**/daily ** - Claim your daily rewards\n**/leaderboard ** - See how you stack up against other players\n**/help ** - Get a list of all available commands and assistance. \n\n*Have fun and good luck! :four_leaf_clover:*')
        await interaction.response.send_message(embed=embed_msg)

class StartButtons(discord.ui.View):
    
    def __init__(self, cog_instance, user_id):
        super().__init__()
        self.cog_instance = cog_instance
        self.user_id = user_id 
        
    @discord.ui.button(label='Create a profile', style=discord.ButtonStyle.green)
    async def create_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user_id:  
            await self.cog_instance.create_user(interaction)
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Profile Created',
                    description="Your profile has been created! 🎉",
                    color=discord.Color.green()
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title='Access Denied',
                    description="You cannot create a profile for another user.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
        
async def setup(bot):
    await bot.add_cog(Start(bot))
