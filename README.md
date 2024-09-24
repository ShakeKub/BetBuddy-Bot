# Discord Gamble Bot 🎲💰

A feature-rich Discord bot written in Python, designed to bring the excitement of gambling and minigames to your server! This bot includes a variety of classic gambling games, an XP system, a leaderboard to track top players, and a robust database for user stats and progress. Perfect for engaging your community with fun and competitive features!

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Commands](#commands)
- [Database](#database)
- [Contributing](#contributing)

 
## Features

- 🎰 **Gambling Games**: Play a range of popular gambling and chance-based games, including:
  - **Roulette**: Bet on red, black, or specific numbers!
  - **Blackjack**: Beat the dealer by getting as close to 21 as possible without busting.
  - **Slots**: Spin the reels and match symbols to win big!
  - **Case Opening**: Open cases to win random virtual rewards.
  - **Dice Game**: Roll a dice and predict the outcome to win!
  - **Hi-Lo**: Guess whether the next card will be higher or lower than the current one.

- 📊 **XP and Leveling System**: 
  - Earn experience points (XP) by playing games and completing challenges.
  - Level up as you progress and show off your achievements on the leaderboard.

- 🏆 **Leaderboard**: 
  - Track your progress against other players on the server.
  - Compete to be the richest and most skilled gambler!

- 🗄️ **Database Support**:
  - Persistent user data storage using SQLite (or any other database).
  - Keep track of player balances, XP, levels, and other statistics.

## Technologies Used

- **Python**: The bot is written in Python, making use of asynchronous programming for efficient performance.
- **discord.py**: A Python wrapper for Discord's API, providing all the necessary functionality to create the bot.
- **SQLite**: A lightweight database solution to store user data like balances, XP, and leaderboard stats.
- **AsyncIO**: To manage asynchronous tasks and ensure smooth bot operation.

## Prerequisites

Before installing the bot, ensure you have the following:

- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **Pip**: Python package installer (comes with Python installation)
- **Discord Bot Token**: Create a bot on the [Discord Developer Portal](https://discord.com/developers/applications) and generate a bot token.

## Installation

To install and set up the bot on your local machine, follow these steps:

1. **Clone the repository** to your local machine:
    ```bash
    git clone https://github.com/ShakeKub/BetBuddy-Bot
    cd BetBuddy-Bot
    ```

2. **Install required dependencies** using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

3. **Create your bot on Discord**:
    - Head to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.
    - Under the "Bot" section, click "Add Bot" and generate a token.
    - Invite your bot to your server using the OAuth2 tab and give it the necessary permissions (e.g., `SEND_MESSAGES`, `MANAGE_MESSAGES`).

## Configuration


After installation, you'll need to configure the bot's settings:

1. **Create a `.env` file** in the root directory of the project and add your Discord bot token:
- Replace `"YOUR_BOT_TOKEN"` with the actual token of your Discord bot.
- You can change the command prefix (default is `!`) and specify the path for the database file.

3. **Database Initialization**:
   - The bot automatically creates the database (SQLite by default) when it runs for the first time. If you're using a different database (like PostgreSQL or MySQL), adjust the code accordingly.

## Usage

Once you've configured the bot, you can run it:

1. **Run the bot**:
    ```bash
    python main.py
    ```

2. **Invite the bot to your server**:
   - Use the OAuth2 link generated in the Discord Developer Portal to invite your bot to the server.

3. **Start interacting**: Use the configured command prefix (default: `/`) to start playing games and interacting with the bot.

## Commands

The bot offers several commands for users to play games, check stats, and interact with the leaderboard.

### Game Commands

- `/roulette ` - Start a game of roulette. Bet on red, black, or specific numbers.
- `/blackjack` - Start a game of blackjack.
- `/slots  [amount]` - Spin the slots for a chance to win!
- `/opencase` - Open a random case to win prizes.

### Player Stats and Leaderboard

- `/stats` - Check your current balance, level and XP.
- `/leaderboard` - Display the server's top players in terms of balance and XP.

### Administrative Commands

- `!reset [user]` - Reset a user's balance or XP (admin-only).
- `!setbalance [user] [amount]` - Set a specific balance for a user (admin-only).

### Fun Extras

- `/daily` - Claim your daily rewards.
- `/help` - Get a list of all commands and their descriptions.

## Database

The bot uses a database to store all relevant player data, including balances, XP, and leaderboards. By default, the bot uses **SQLite** for simple local storage, but you can modify the code to use other databases like **PostgreSQL** or **MySQL** if required.

- **Schema**:
  - Users table: stores user IDs, balances, XP, and levels.
  - Transactions table: logs all bets and payouts for transparency.
  
The database is automatically initialized when the bot is run for the first time.


---

Enjoy the gamble bot and have fun! If you encounter any issues, feel free to reach out or create an issue in the repository.
