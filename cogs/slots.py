import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import sqlite3
import asyncio

class SlotsGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_bet_amount = {}
        self.last_biggest_win = {}

    symbols = ["🍒", "🍋", "🍉", "🍇", "💎", "🔔"]
    payout_table = {
        "🍒🍒🍒": 7, "🍋🍋🍋": 7, "🍉🍉🍉": 7, "🍇🍇🍇": 7, "💎💎💎": 20, "🔔🔔🔔": 7,
        "🍒🍒🍋": 1.4, "🍒🍒🍉": 3, "🍒🍋🍋": 1.4, "🍒🍉🍉": 1.4, "🍒🍋🍉": 1.7,
        "🍋🍉🍉": 1.4, "🍉🍉🍇": 1.4, "🍉🍇🍇": 1.4, "🔔🔔🍒": 1.4, "🔔🍒🍋": 1.6,
        "🔔🍒🍉": 3, "💎💎🍒": 1.4, "💎💎🍋": 2.2, "💎🍒🍋": 1.5,
    }

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

    async def choose_bet_amount(self, interaction: discord.Interaction, message=None, bet_amount=None):
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
        chip_emoji = self.get_chip_emoji(current_chips)

        if current_chips <= 0:
            await interaction.response.send_message("You do not have enough chips to place a bet. Please earn or deposit more chips.")
            return

        if bet_amount is None:
            await interaction.response.send_message("Please specify a bet amount using `/slots <chips>`.")
            return

        if bet_amount > current_chips:
            await interaction.response.send_message("You do not have enough chips to place this bet.")
            return

        self.last_bet_amount[user_id] = bet_amount
        await self.spin_slots(interaction, message, bet_amount, bet_amount == current_chips)

    async def spin_slots(self, interaction: discord.Interaction, message, bet_amount, all_in):
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
        chip_emoji = self.get_chip_emoji(current_chips)

        if bet_amount > 0 and not all_in:
            self.update_chips(user_id, bet_amount, increase=False)

        spinning_embed = discord.Embed(
            title=f"{interaction.user.name}'s Slot Machine",
            description=(
                f"Pocket: {current_chips} {chip_emoji}\n"
                f"Winnings: 0 {chip_emoji}\n"
                f"Bet: {bet_amount} {chip_emoji}\n\n"
                "🍒 | 🍋 | 🍊\n"
                "🍉 | 🍇 | 🍓\n"
                "🍍 | 🍑 | 🔔"
            ),
            color=0x2F3136
        )
        await interaction.response.send_message(embed=spinning_embed)
        message = await interaction.original_response()

        spin_iterations = 10
        for _ in range(spin_iterations):
            spin_result = [random.choice(self.symbols) for _ in range(9)]
            spin_str = (
                ' | '.join(spin_result[:3]) + "\n" +
                ' | '.join(spin_result[3:6]) + "\n" +
                ' | '.join(spin_result[6:])
            )
            spinning_embed.description = (
                f"Pocket: {current_chips} {chip_emoji}\n"
                f"Winnings: 0 {chip_emoji}\n"
                f"Bet: {bet_amount} {chip_emoji}\n\n"
                f"{spin_str}"
            )
            await message.edit(embed=spinning_embed)
            await asyncio.sleep(0.1)

        spin_result = [random.choice(self.symbols) for _ in range(9)]
        result_str = (
            ' | '.join(spin_result[:3]) + "\n" +
            ' | '.join(spin_result[3:6]) + "\n" +
            ' | '.join(spin_result[6:])
        )

        row1 = ''.join(spin_result[:3])
        row2 = ''.join(spin_result[3:6])
        row3 = ''.join(spin_result[6:])

        winnings = 0

        if row1 in self.payout_table:
            winnings += bet_amount * self.payout_table[row1]
        if row2 in self.payout_table:
            winnings += bet_amount * self.payout_table[row2]
        if row3 in self.payout_table:
            winnings += bet_amount * self.payout_table[row3]

        result_embed = discord.Embed(
            title=f"{interaction.user.name}'s Slot Machine",
            description=(
                f"Pocket: {current_chips} {chip_emoji}\n"
                f"Winnings: {winnings} {chip_emoji}\n"
                f"Bet: {bet_amount} {chip_emoji}\n\n"
                f"{result_str}"
            ),
            color=0x3498db
        )

        if winnings > 0:
            result_embed.color = 0x90ee90
            result_embed.set_footer(text="Congratulations! 🎉")
            self.last_biggest_win[user_id] = winnings
            self.update_chips(user_id, winnings, increase=True)
        else:
            result_embed.color = 0xff0000
            result_embed.set_footer(text="Better luck next time! 😢")
            if all_in:
                self.update_chips(user_id, bet_amount, increase=False)

        #replay_button = Button(label="Play Again", style=discord.ButtonStyle.primary, custom_id="replay")
        quit_button = Button(label="Quit", style=discord.ButtonStyle.danger, custom_id="quit")

        final_view = View()
        #final_view.add_item(replay_button)
        final_view.add_item(quit_button)

        await message.edit(embed=result_embed, view=final_view)

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            if inter.data['custom_id'] == "replay":
                # Ensure that the original interaction is not responded to again
                print("Replay button clicked.")  # Debug print
                await self.choose_bet_amount(interaction, message=message, bet_amount=self.last_bet_amount.get(user_id))
            elif inter.data['custom_id'] == "quit":
                print("Quit button clicked.")  # Debug print
                del self.last_bet_amount[interaction.user.id]
                await message.delete()
        except Exception as e:
            print(f"Interaction failed with error: {e}")
            await message.delete()

    def update_chips(self, user_id, amount, increase):
        conn = sqlite3.connect('discord_database.db')
        cursor = conn.cursor()
        if increase:
            cursor.execute('UPDATE users SET chips = chips + ?, xp = xp + ? WHERE user_id = ?', (amount, 2, user_id))
        else:
            cursor.execute('UPDATE users SET chips = chips - ?, xp = xp + ? WHERE user_id = ?', (amount, 2, user_id))
        conn.commit()
        conn.close()

    @discord.app_commands.command(name="slots", description="Play a slot machine game!")
    @discord.app_commands.describe(chips="Amount of chips to bet")
    async def slots(self, interaction: discord.Interaction, chips: int):
        start_cog = self.bot.get_cog('Start')
        user_exists = await start_cog.check_for_user(interaction)
        if user_exists:
            await self.choose_bet_amount(interaction, bet_amount=chips)
        else:
            await start_cog.show_menu(interaction)

async def setup(bot):
    await bot.add_cog(SlotsGame(bot))
