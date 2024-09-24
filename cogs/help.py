import discord
from discord import app_commands
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='Lists available commands and their descriptions.')
    async def help_command(self, interaction: discord.Interaction):
        start_cog = self.bot.get_cog('Start')

        user_exists = await start_cog.check_for_user(interaction)
        if user_exists:
            embed = discord.Embed(
                title="Help - Available Commands",
                description="Here are the commands you can use:",
                color=discord.Color(0x2F3136)
            )

            embed.add_field(
                name="Casino Games",
                value=(
                    "• /slots - Play a slot machine game. <:slots:1278993029801185330>\n"
                    "• /blackjack - Play a card game called Blackjack. <:card_spades:1278709573326344325>\n"
                    "• /roulette - lay a board game called Roulette. <:roulette:1278998129064284211>\n"
                    "• /hilo - Play a number game called High Low. <:card_hearts:1278709580934680717>\n"
                    "• /dice - Play a dice game called the Dice <:dice:1278709560600956980>\n" 
                    "• /opencase - Play a opening game call Case opening\n"
                ),
                inline=False  
            )


            embed.add_field(
                name="\u200b",  
                value="\u200b",  
                inline=False
            )

            embed.add_field(
                name="General Help",
                value=(
                    "/stats - Shows stats about the user.\n"
                    "/leaderboard - Display the top 5 richest users.\n"
                    "/daily - Get free chips from daily reward.\n"
                    "/claim - Claim your reward every 5 minutes.\n"
                    "/transfer - Transfer chips from your wallet to another player.\n"
                ),
                inline=False  
            )

            embed.set_footer(text="ouje")

            await interaction.response.send_message(embed=embed)
        else:
            await start_cog.show_menu(interaction)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
