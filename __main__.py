from webserver import keep_alive
import discord
from discord.ext import commands
from config import config


bot = commands.Bot(command_prefix=config.BOT_PREFIX,
                   intents=discord.Intents.all())


if __name__=="__main__":

    if config.BOT_TOKEN=='':
        print("Error: No bot token!")
        exit


@bot.event
async def on_ready():
    print(config.STARTUP_MESSAGE)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f"Число слушателей {0}"))
    for guild in bot.guilds:
        
        print(f"Joined {guild.name}")

    print(config.STARTUP_COMPLETE_MESSAGE)


keep_alive()
bot.run(config.BOT_TOKEN)