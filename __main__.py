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


#Adding new users in DB and asking then to reg
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
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=f"debuging")) #Введите {config.BOT_PREFIX}help

    for guild in bot.guilds:
        print(f"Joined {guild.name}")  

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

@bot.command() 
async def reg(ctx: commands.Context):
    await ctx.message.delete()

    guild = ctx.message.guild
    member = ctx.author
    overwrites = {                                                             #Права для чата регистрации
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True),
    }

    categorie = discord.utils.get(guild.categories, name='Регистрация')
    if categorie is None: 
        categorie = await guild.create_category('Регистрация')
    
    regchen = discord.utils.get(categorie.channels, name=f'Регистрация {member}')
    if regchen is None:
        channel = await guild.create_text_channel(f'регистрация {member}', 
                                                overwrites=overwrites, 
                                                position=0,
                                                topic='Зарегистрируйся, чтобы посещать лекции',
                                                slowmode_delay=30,
                                                category=categorie,
                                                default_auto_archive_duration=1440)
    
    

keep_alive()
bot.run(config.BOT_TOKEN)