import discord
from discord import app_commands
from discord.ext import commands

class InviteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='invite', description='Get an invite link to add the bot to your server.')
    async def invite(self, interaction: discord.Interaction):
        
        invite_link = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(permissions=1689831260814400))

        
        embed = discord.Embed(
            title="Invite BetBuddy to Your Server!",
            description="BetBuddy is a gambling bot that lets you play various casino-style games such as blackjack, roulette, and more. Compete with other users and climb the leaderboard!",
            color=discord.Color(0x2F3136)
        )
        
        embed.add_field(name="Features", value="""
        \n**🎰 Variety of Games:** Try out blackjack, roulette, and more.
        \n**🏆 Leaderboards:** See who the richest users are.
        \n**🎁 Daily Rewards:** Claim your daily chips and keep playing.
        \n**🎉 Fun and Engaging:** Join in on the excitement with your friends!
        """, inline=False)

        embed.add_field(name="Invite Link", value=f"**[Click here to invite BetBuddy]({invite_link})**", inline=False)
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text="Join the fun and gamble responsibly!")

        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(InviteCog(bot))
