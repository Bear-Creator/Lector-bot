from webserver import keep_alive
import discord
from discord.ext import commands
import sqlite3
from config import config


db = sqlite3.connect('server.db')
cursor = db.cursor()
bot = commands.Bot(command_prefix=config.BOT_PREFIX,
                   intents=discord.Intents.all())


if __name__=="__main__":

    if config.BOT_TOKEN=='':
        print("Error: No bot token!")
        exit


async def guild_reg(guilde: discord.Guild):
    cursor.execute(

    )


@bot.event
async def on_ready():
    print(config.STARTUP_MESSAGE)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f"Введите {config.BOT_PREFIX}help"))

    for guild in bot.guilds:
        
        cursor.execute(
            f'''CREATE TABLE if NOT EXISTS users (
            id          int NOT NULL,
            username    varchar(80)
            PRIMARY KEY (id)
            );'''
        )

        db.commit()

        print(f"Joined {guild.name}")

    print(config.STARTUP_COMPLETE_MESSAGE)


keep_alive()
bot.run(config.BOT_TOKEN)