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
            temp_grp  int,
            FOREIGN KEY (sid) REFERENCES students (id)
            );'''
        )
        
        for member in guild.members:
            await new_user(member)
        db.commit()
        
        global role_autho
        role_autho = discord.utils.get(guild.roles, name = config.ROLE_AUTHORIZED_NAME)
        permissions = discord.Permissions(**config.ROLE_AUTHORIZED_PERMISSIONS)
        if role_autho is None:
            role_autho = await guild.create_role(name=config.ROLE_AUTHORIZED_NAME, permissions=permissions)

    print(config.STARTUP_COMPLETE_MESSAGE)


@bot.event
async def on_raw_reaction_add(reaction: discord.raw_models.RawReactionActionEvent):
    guild = bot.get_guild(reaction.guild_id)
    member = reaction.member
    overwrites = {                                                             #Права для чата регистрации
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True),
    }

    ChID = discord.utils.get(guild.channels, name='вход').id
    if reaction.channel_id == ChID and reaction.emoji.name == '✅':
        
        categorie = discord.utils.get(guild.categories, name='Регистрация')
        if categorie is None: 
            categorie = await guild.create_category('Регистрация')

        regchen = discord.utils.get(categorie.channels, name=f'регистрация-{str(member).replace("#", "").replace(" ", "-")}' )
        if regchen is not None:
            await regchen.delete()
        
        regchen = await guild.create_text_channel(f'Регистрация-{member}', 
                                                overwrites=overwrites, 
                                                position=0,
                                                topic='Зарегистрируйся, чтобы посещать лекции',
                                                slowmode_delay=10,
                                                category=categorie,
                                                default_auto_archive_duration=1440)

        await regchen.send(f'{member.mention}, напишите, пожалуйста, вашу группу')


@bot.event
async def on_message(msg: discord.Message):
    author = msg.author
    channel = msg.channel
    text = msg.content
    guild = msg.guild
    if author.bot:
        return

    print(f'{author}: {text}')
    
    if 'регистрация' in channel.name:

        groups = [i[0] for i in set(cursor.execute('SELECT grp FROM students;'))]
        group = cursor.execute(f'SELECT temp_grp FROM users_{guild.id} WHERE id == {author.id};').fetchone()[0]

        if group is None and text in map(str, groups):

            cursor.execute( f'UPDATE users_{guild.id} SET temp_grp={int(text)} WHERE id = {author.id};' )
            db.commit()

            await msg.reply('Отлично, теперь введите ваше полное имя в форме ФИО')
            return

        elif group is None:

            await msg.reply('Извените, Вашей группы ещё нет в базе. Обратитесь к администратору!')
            return
        
        student = cursor.execute(f'SELECT * FROM students WHERE name = "{text}";').fetchone()
        if student[1] != group:

            cursor.execute(f'UPDATE users_{guild.id} DELETE temp_grp WHERE id = {author.id};')
            db.commit()

            await msg.reply('Данные введены неверно! Попробуде ещё раз')
            channel.delete()

            return
        
        cursor.execute(f'UPDATE users_{guild.id} SET sid = {student[0]} WHERE id = {author.id};')
        db.commit()

        name = text.split()
        if len(' '.join(name[:2])) <= 32:
            name = ' '.join(name[:2])
        elif len(name[0]) <= 32:
            name = name[0]
        else:
            name = name[:32]

        await author.edit(nick=name)
        await author.add_roles(role_autho)
        await channel.send('Вы успешно авторизовалисть!')
        await channel.delete()

 

    await bot.process_commands(msg)


keep_alive()
bot.run(config.BOT_TOKEN)