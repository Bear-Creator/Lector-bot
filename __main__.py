from webserver import keep_alive
import discord
from discord.ext import commands
import sqlite3
from config import config
from lib.mytools import *


db = sqlite3.connect(config.DB_LINK_SERVER)
cursor = db.cursor()
bot = commands.Bot(command_prefix=config.BOT_PREFIX,
                   intents=discord.Intents.all())


async def new_user(member: discord.Member):

    if (cursor.execute(
        f'SELECT id FROM users_{member.guild.id} WHERE id == {member.id};').fetchone() is not None
        ) or (member == bot.user):
        return
    
    cursor.execute(f'INSERT INTO users_{member.guild.id} (id)VALUES ({member.id});')
    db.commit()

    if (member.guild.id != config.GUILDE_ID): #Костыль - бот не может получить reg беседу для каждой гильдии
        return
    await bot.get_channel(config.REGISTRATION_CHANNEL).send(f'<@{member.id}>, пройдите регистрацию. Отправьте {config.BOT_PREFIX}reg')


if __name__=="__main__":

    if config.BOT_TOKEN=='':
        print("Error: No bot token!")
        exit

    copy_table(config.DB_LINK_STUDLIST, config.DB_LINK_SERVER, 'students')


@bot.event
async def on_ready():
    print(config.STARTUP_MESSAGE)
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f"Введите {config.BOT_PREFIX}help"))

    for guild in bot.guilds:
        print(f"Joined {guild.name}", guild.id)

        cursor.execute(
            f'''CREATE TABLE if NOT EXISTS users_{guild.id} (
            id        int,
            sid       int,
            FOREIGN KEY (sid) REFERENCES students (id)
            );'''
        )
        
        for member in guild.members:
            await new_user(member)
        db.commit()
    
    print(config.STARTUP_COMPLETE_MESSAGE)


keep_alive()
bot.run(config.BOT_TOKEN)