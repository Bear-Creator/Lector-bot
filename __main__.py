from mylib.webserver import keep_alive
import discord
from discord.ext import commands
import sqlite3
import time
import os
from config import config
from mylib.mytools import *


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

@bot.command(help = 'Считает количество участников в голосовом чате')
@commands.has_any_role('Лектор', 'Администратор')
async def count(ctx: commands.Context):
    voice = discord.utils.get(ctx.guild.voice_channels, name="Лекция")
    stud = voice.members
    f =  open('cash/studlist.txt', 'w')
    for std in stud:
        cursor.execute(f'SELECT students.name, students.grp FROM users_{ctx.guild.id}, students WHERE users_{ctx.guild.id}.id = {std.id};')
        print(std.nick, file=f)
    f.close()
    await ctx.send(file=discord.File(r'cash/studlist.txt'))
    os.remove('cash/studlist.txt')
    return

@bot.command(help = 'deletes users information')
@commands.has_any_role('Администратор')
async def delusr(ctx: commands.Context, arg: str):
    member = discord.utils.get(ctx.guild.members, id=int(arg))
    for role in member.roles[1:]:
        print(role)
        await member.remove_roles(role)
    await member.edit(nick=None)
    cursor.execute(f'DELETE FROM users_{member.guild.id} WHERE id = {int(arg)};')
    await new_user(member)
    await ctx.reply(f'Пользователь {member} удалён.')
    await ctx.message.delete()

@bot.command()
async def test(ctx: commands.Context):

    roles = ctx.author.roles

    otvet = f'{roles}'
    await ctx.reply(otvet)
    await ctx.message.delete()
    pass

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
        

        role_autho = discord.utils.get(guild.roles, name = config.ROLE_AUTHORIZED_NAME)
        permissions = discord.Permissions(**config.ROLE_AUTHORIZED_PERMISSIONS)
        if role_autho is None:
            role_autho = await guild.create_role(name=config.ROLE_AUTHORIZED_NAME, permissions=permissions)

    print(config.STARTUP_COMPLETE_MESSAGE)

@bot.event
async def on_member_join(member):
    await new_user(member)

@bot.event
async def on_member_remove(member: discord.Member):
    cursor.execute(f'DELETE FROM users_{member.guild.id} WHERE id = {member.id};')

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

        regchen = discord.utils.get(categorie.channels, name=f'регистрация-{str(member).replace("#", "").replace(" ", "-").lower()}' )
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
        if discord.utils.get(author.roles, name='Администратор') is not None:
            return

        groups = [i[0] for i in set(cursor.execute('SELECT grp FROM students;'))]
        group = cursor.execute(f'SELECT temp_grp FROM users_{guild.id} WHERE id == {author.id};').fetchone()[0]


        if group is None and text in map(str, groups):

            cursor.execute( f'UPDATE users_{guild.id} SET temp_grp={int(text)} WHERE id = {author.id};' )
            db.commit()

            await msg.reply('Отлично, теперь введите ваше полное имя в форме ФИО')
            return

        elif group is None:

            await msg.reply('Извините, введите группу ещё раз, либо обратитесь к администратору при повторной ошибке.')
            # time.sleep(20)
            # await channel.delete()
            return
        
        
        student = cursor.execute(f'SELECT * FROM students WHERE name = "{text.lower()}";').fetchone()
        if student is None:
            await msg.reply('ФИО введено неверно. Проверьте данные и попробуйте ещё раз, при повторной ошибке обратитесь к администратору.')
            # time.sleep(10)
            cursor.execute(f'UPDATE users_{guild.id} SET temp_grp=null WHERE id = {author.id};')
            db.commit()
            # await channel.delete()
            return

        if student[1] != group:
            await msg.reply('ФИО введено неверно. Проверьте данные и попробуйте ещё раз, при повторной ошибке обратитесь к администратору.')
            # time.sleep(10)
            cursor.execute(f'UPDATE users_{guild.id} SET temp_grp=null WHERE id = {author.id};')
            db.commit()
            # await channel.delete()
            return
        
        if cursor.execute(f'SELECT sid FROM users_{guild.id} WHERE sid = {student[0]};').fetchone() is not None:
            
            await msg.reply('Кто-то уже вошёл под этим именем. Если это были не вы, обратитесь к администратору!')
            # time.sleep(20)
            cursor.execute(f'UPDATE users_{guild.id} SET temp_grp=null WHERE id = {author.id};')
            db.commit()
            # await channel.delete()
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
        await author.add_roles(discord.utils.get(guild.roles, name = config.ROLE_AUTHORIZED_NAME))
        await channel.send('Вы успешно авторизовалисть!')
        time.sleep(10)
        await channel.delete()

 

    await bot.process_commands(msg)


keep_alive()
bot.run(config.BOT_TOKEN)