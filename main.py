import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv  

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Bot {bot.user} je přihlášen a připraven!')
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="/help"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Tento příkaz neexistuje.")
    else:
        raise error

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            cog_name = filename[:-3]
            if cog_name in bot.cogs:
                print(f'{cog_name} is already loaded.')
            else:
                try:
                    await bot.load_extension(f'cogs.{cog_name}')
                    print(f'Loaded extension {cog_name}.')
                except discord.ClientException as e:
                    print(f'Failed to load extension {cog_name}: {e}')

async def main():
    await load_extensions()
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
