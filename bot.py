import discord
from discord.ext import commands
import json
import os
import random
import asyncio
from datetime import datetime, timedelta

TOKEN = ""

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

if not os.path.exists("levels.json"):
    with open("levels.json", "w") as f:
        json.dump({}, f)

if not os.path.exists("shop.json"):
    with open("shop.json", "w") as f:
        json.dump({}, f)

if not os.path.exists("marriage.json"):
    with open("marriage.json", "w") as f:
        json.dump({}, f)

if not os.path.exists("friends.json"):
    with open("friends.json", "w") as f:
        json.dump({}, f)

if not os.path.exists("daily_tasks.json"):
    with open("daily_tasks.json", "w") as f:
        json.dump({}, f)


def load_data():
    with open("levels.json", "r") as f:
        return json.load(f)


def save_data(data):
    with open("levels.json", "w") as f:
        json.dump(data, f, indent=4)


def load_marriage():
    with open("marriage.json", "r") as f:
        return json.load(f)


def save_marriage(data):
    with open("marriage.json", "w") as f:
        json.dump(data, f, indent=4)


def load_friends():
    with open("friends.json", "r") as f:
        return json.load(f)


def save_friends(data):
    with open("friends.json", "w") as f:
        json.dump(data, f, indent=4)


def load_tasks():
    with open("daily_tasks.json", "r") as f:
        return json.load(f)


def save_tasks(data):
    with open("daily_tasks.json", "w") as f:
        json.dump(data, f, indent=4)


WELCOME_CHANNEL_ID = None
VOICE_XP = {}
CASINO_COOLDOWN = {}
CASINO_WINS = {}


@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")
    await bot.change_presence(activity=discord.Game(name="!shop | !casino | !daily | !marry"))


@bot.event
async def on_member_join(member):
    data = load_data()
    user_id = str(member.id)

    if user_id not in data:
        data[user_id] = {"xp": 0, "level": 0, "total_xp": 0}

    data[user_id]["xp"] += 50
    data[user_id]["total_xp"] += 50

    while data[user_id]["xp"] >= (data[user_id]["level"] + 1) * 100:
        data[user_id]["xp"] -= (data[user_id]["level"] + 1) * 100
        data[user_id]["level"] += 1

    save_data(data)

    if WELCOME_CHANNEL_ID:
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Новый участник!",
                description=f"Здравствуйте, {member.mention}!",
                color=0x00ff00
            )
            embed.add_field(name="Бонус", value="Вы получили 50 опыта за вход на сервер")
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text="Пишите в чат и сидите в голосовых каналах чтобы получать опыт")
            await channel.send(embed=embed)


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        VOICE_XP[member.id] = {"start": datetime.now(), "channel": after.channel.id}

    elif before.channel is not None and after.channel is None:
        if member.id in VOICE_XP:
            start_time = VOICE_XP[member.id]["start"]
            minutes = (datetime.now() - start_time).seconds // 60
            if minutes >= 1:
                xp_gain = minutes * 5
                data = load_data()
                user_id = str(member.id)
                if user_id not in data:
                    data[user_id] = {"xp": 0, "level": 0, "total_xp": 0}
                data[user_id]["xp"] += xp_gain
                data[user_id]["total_xp"] += xp_gain

                while data[user_id]["xp"] >= (data[user_id]["level"] + 1) * 100:
                    data[user_id]["xp"] -= (data[user_id]["level"] + 1) * 100
                    data[user_id]["level"] += 1
                    channel = bot.get_channel(after.channel.id) if after.channel else None
                    if channel and channel.guild.system_channel:
                        await channel.guild.system_channel.send(
                            f"{member.mention} повысился до {data[user_id]['level']} уровня!")

                save_data(data)
            del VOICE_XP[member.id]


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()
    user_id = str(message.author.id)

    if user_id not in data:
        data[user_id] = {"xp": 0, "level": 0, "total_xp": 0}

    data[user_id]["xp"] += 5
    data[user_id]["total_xp"] += 5

    while data[user_id]["xp"] >= (data[user_id]["level"] + 1) * 100:
        data[user_id]["xp"] -= (data[user_id]["level"] + 1) * 100
        data[user_id]["level"] += 1
        await message.channel.send(f"{message.author.mention} повысился до {data[user_id]['level']} уровня!")

    save_data(data)
    await bot.process_commands(message)


@bot.command()
async def rank(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    data = load_data()
    user_id = str(member.id)

    if user_id not in data:
        await ctx.send(f"{member.mention} ещё не имеет опыта")
        return

    level = data[user_id]["level"]
    xp = data[user_id]["xp"]
    total_xp = data[user_id]["total_xp"]
    xp_needed = (level + 1) * 100

    embed = discord.Embed(title=f"Уровень {member.name}", color=0x00ff00)
    embed.add_field(name="Уровень", value=level)
    embed.add_field(name="Опыт", value=f"{xp}/{xp_needed}")
    embed.add_field(name="Всего опыта получено", value=total_xp)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel_id: int):
    global WELCOME_CHANNEL_ID
    WELCOME_CHANNEL_ID = channel_id
    await ctx.send(f"Канал приветствий настроен. ID: {channel_id}")


@bot.command()
async def shop(ctx):
    embed = discord.Embed(title="Магазин ролей", description="Покупай роли за опыт", color=0x00ff00)
    embed.add_field(name="1. Новичок", value="Стоимость: 100 опыта")
    embed.add_field(name="2. Активный", value="Стоимость: 300 опыта")
    embed.add_field(name="3. Ветеран", value="Стоимость: 600 опыта")
    embed.add_field(name="4. Элита", value="Стоимость: 1000 опыта")
    embed.add_field(name="5. Легенда", value="Стоимость: 2000 опыта | Шанс 30%")
    embed.add_field(name="6. VIP", value="Стоимость: 5000 опыта | Шанс 10%")
    embed.set_footer(text="Используй: !buy [номер]")
    await ctx.send(embed=embed)


@bot.command()
async def buy(ctx, item_id: int):
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data:
        await ctx.send("У вас нет опыта")
        return

    total_xp = data[user_id]["total_xp"]

    shop_items = {
        1: {"name": "Новичок", "price": 100, "chance": 100},
        2: {"name": "Активный", "price": 300, "chance": 100},
        3: {"name": "Ветеран", "price": 600, "chance": 100},
        4: {"name": "Элита", "price": 1000, "chance": 100},
        5: {"name": "Легенда", "price": 2000, "chance": 30},
        6: {"name": "VIP", "price": 5000, "chance": 10}
    }

    if item_id not in shop_items:
        await ctx.send("Неверный номер товара. Используй !shop")
        return

    item = shop_items[item_id]

    if total_xp < item["price"]:
        await ctx.send(f"Не хватает опыта. Нужно: {item['price']}, у вас: {total_xp}")
        return

    if item["chance"] < 100:
        roll = random.randint(1, 100)
        if roll > item["chance"]:
            await ctx.send(f"Не повезло! Вы не получили роль {item['name']}. Шанс был {item['chance']}%")
            return

    data[user_id]["total_xp"] -= item["price"]
    save_data(data)

    role = discord.utils.get(ctx.guild.roles, name=item["name"])
    if not role:
        role = await ctx.guild.create_role(name=item["name"])

    await ctx.author.add_roles(role)
    await ctx.send(f"Поздравляю! Вы купили роль {item['name']} за {item['price']} опыта")


@bot.command()
async def casino(ctx, bet: int = 15):
    user_id = ctx.author.id
    now = datetime.now()

    if user_id in CASINO_COOLDOWN:
        time_diff = (now - CASINO_COOLDOWN[user_id]).seconds
        if time_diff < 300:
            remaining = 300 - time_diff
            minutes = remaining // 60
            seconds = remaining % 60
            await ctx.send(f"Подожди {minutes} мин {seconds} сек до следующей прокрутки казино")
            return

    data = load_data()
    user_id_str = str(user_id)

    if user_id_str not in data:
        await ctx.send("У вас нет опыта")
        return

    if bet < 15:
        await ctx.send("Минимальная ставка: 15 опыта")
        return

    if data[user_id_str]["total_xp"] < bet:
        await ctx.send(f"Не хватает опыта. У вас: {data[user_id_str]['total_xp']}")
        return

    outcomes = [
        {"gain": -15, "chance": 45, "text": "Проигрыш! -15 опыта"},
        {"gain": 0, "chance": 15, "text": "Ничья! 0 опыта"},
        {"gain": 5, "chance": 12, "text": "Маленький выигрыш! +5 опыта"},
        {"gain": 10, "chance": 10, "text": "Неплохо! +10 опыта"},
        {"gain": 15, "chance": 8, "text": "Хорошо! +15 опыта"},
        {"gain": 20, "chance": 5, "text": "Отлично! +20 опыта"},
        {"gain": 30, "chance": 3, "text": "Крупно! +30 опыта"},
        {"gain": 50, "chance": 1.5, "text": "ДЖЕКПОТ! +50 опыта"},
        {"gain": 100, "chance": 0.4, "text": "МЕГА ДЖЕКПОТ! +100 опыта"},
        {"gain": 250, "chance": 0.1, "text": "НЕВЕРОЯТНО! +250 опыта"}
    ]

    roll = random.random() * 100
    cumulative = 0
    selected = outcomes[-1]

    for outcome in outcomes:
        cumulative += outcome["chance"]
        if roll <= cumulative:
            selected = outcome
            break

    xp_gain = selected["gain"]

    if xp_gain > 0:
        if user_id_str not in CASINO_WINS:
            CASINO_WINS[user_id_str] = 0
        CASINO_WINS[user_id_str] += 1

    data[user_id_str]["total_xp"] += xp_gain
    data[user_id_str]["xp"] += xp_gain

    while data[user_id_str]["xp"] < 0:
        if data[user_id_str]["level"] > 0:
            data[user_id_str]["level"] -= 1
            data[user_id_str]["xp"] += (data[user_id_str]["level"] + 1) * 100
        else:
            data[user_id_str]["xp"] = 0
            break

    while data[user_id_str]["xp"] >= (data[user_id_str]["level"] + 1) * 100:
        data[user_id_str]["xp"] -= (data[user_id_str]["level"] + 1) * 100
        data[user_id_str]["level"] += 1
        await ctx.send(f"{ctx.author.mention} повысился до {data[user_id_str]['level']} уровня благодаря казино!")

    save_data(data)
    CASINO_COOLDOWN[user_id] = now

    embed = discord.Embed(title="Казино", description=selected["text"], color=0x00ff00 if xp_gain >= 0 else 0xff0000)
    embed.add_field(name="Результат", value=f"{'+' if xp_gain >= 0 else ''}{xp_gain} опыта")
    embed.add_field(name="Ваш баланс опыта", value=data[user_id_str]["total_xp"])
    await ctx.send(embed=embed)


@bot.command()
async def daily(ctx):
    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data:
        data[user_id] = {"xp": 0, "level": 0, "total_xp": 0}

    bonus = random.randint(30, 100)
    data[user_id]["total_xp"] += bonus
    data[user_id]["xp"] += bonus

    while data[user_id]["xp"] >= (data[user_id]["level"] + 1) * 100:
        data[user_id]["xp"] -= (data[user_id]["level"] + 1) * 100
        data[user_id]["level"] += 1
        await ctx.send(f"{ctx.author.mention} повысился до {data[user_id]['level']} уровня от ежедневного бонуса!")

    save_data(data)
    await ctx.send(f"Ежедневный бонус! Вы получили {bonus} опыта")


@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    data = load_data()
    user_id = str(ctx.author.id)
    target_id = str(member.id)

    if user_id not in data or data[user_id]["total_xp"] < amount:
        await ctx.send("Не хватает опыта для перевода")
        return

    if amount < 1:
        await ctx.send("Сумма перевода должна быть положительной")
        return

    if target_id not in data:
        data[target_id] = {"xp": 0, "level": 0, "total_xp": 0}

    data[user_id]["total_xp"] -= amount
    data[user_id]["xp"] -= amount

    if data[user_id]["xp"] < 0:
        if data[user_id]["level"] > 0:
            data[user_id]["level"] -= 1
            data[user_id]["xp"] += (data[user_id]["level"] + 1) * 100
        else:
            data[user_id]["xp"] = 0

    data[target_id]["total_xp"] += amount
    data[target_id]["xp"] += amount

    while data[target_id]["xp"] >= (data[target_id]["level"] + 1) * 100:
        data[target_id]["xp"] -= (data[target_id]["level"] + 1) * 100
        data[target_id]["level"] += 1
        await ctx.send(f"{member.mention} повысился до {data[target_id]['level']} уровня!")

    save_data(data)
    await ctx.send(f"{ctx.author.mention} перевёл {amount} опыта {member.mention}")


@bot.command()
async def top(ctx):
    data = load_data()
    sorted_users = sorted(data.items(), key=lambda x: x[1]["total_xp"], reverse=True)[:10]

    embed = discord.Embed(title="Топ-10 по опыту", color=0x00ff00)

    for i, (user_id, stats) in enumerate(sorted_users, 1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(name=f"{i}. {user.name}", value=f"Уровень: {stats['level']} | Опыт: {stats['total_xp']}",
                        inline=False)

    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def addxp(ctx, member: discord.Member, amount: int):
    data = load_data()
    user_id = str(member.id)

    if user_id not in data:
        data[user_id] = {"xp": 0, "level": 0, "total_xp": 0}

    data[user_id]["total_xp"] += amount
    data[user_id]["xp"] += amount

    while data[user_id]["xp"] >= (data[user_id]["level"] + 1) * 100:
        data[user_id]["xp"] -= (data[user_id]["level"] + 1) * 100
        data[user_id]["level"] += 1

    save_data(data)
    await ctx.send(f"Добавлено {amount} опыта {member.mention}")


@bot.command()
async def marry(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("Нельзя жениться на себе")
        return

    if member.bot:
        await ctx.send("Нельзя жениться на боте")
        return

    marriage_data = load_marriage()
    user_id = str(ctx.author.id)
    target_id = str(member.id)

    if user_id in marriage_data:
        await ctx.send("Вы уже состоите в браке. Используйте !divorce для развода")
        return

    if target_id in marriage_data:
        await ctx.send(f"{member.mention} уже состоит в браке")
        return

    marriage_data[user_id] = target_id
    marriage_data[target_id] = user_id
    save_marriage(marriage_data)

    embed = discord.Embed(title="Брак заключён!", color=0xff00ff)
    embed.add_field(name="Пара", value=f"{ctx.author.mention} и {member.mention}")
    embed.add_field(name="Дата", value=datetime.now().strftime("%d.%m.%Y %H:%M"))
    await ctx.send(embed=embed)


@bot.command()
async def divorce(ctx):
    marriage_data = load_marriage()
    user_id = str(ctx.author.id)

    if user_id not in marriage_data:
        await ctx.send("Вы не состоите в браке")
        return

    partner_id = marriage_data[user_id]
    del marriage_data[user_id]
    del marriage_data[partner_id]
    save_marriage(marriage_data)

    await ctx.send(f"{ctx.author.mention} развёлся. Грустно")


@bot.command()
async def partner(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    marriage_data = load_marriage()
    user_id = str(member.id)

    if user_id not in marriage_data:
        await ctx.send(f"{member.mention} не состоит в браке")
        return

    partner_id = marriage_data[user_id]
    partner = await bot.fetch_user(int(partner_id))

    embed = discord.Embed(title="Информация о браке", color=0xff00ff)
    embed.add_field(name="Участник", value=member.mention)
    embed.add_field(name="Партнёр", value=partner.mention)
    await ctx.send(embed=embed)


@bot.command()
async def addfriend(ctx, member: discord.Member):
    if member == ctx.author:
        await ctx.send("Нельзя добавить в друзья самого себя")
        return

    friends_data = load_friends()
    user_id = str(ctx.author.id)
    target_id = str(member.id)

    if user_id not in friends_data:
        friends_data[user_id] = []

    if target_id in friends_data[user_id]:
        await ctx.send(f"{member.mention} уже в ваших друзьях")
        return

    friends_data[user_id].append(target_id)
    save_friends(friends_data)
    await ctx.send(f"{ctx.author.mention} добавил {member.mention} в друзья!")


@bot.command()
async def removefriend(ctx, member: discord.Member):
    friends_data = load_friends()
    user_id = str(ctx.author.id)
    target_id = str(member.id)

    if user_id not in friends_data or target_id not in friends_data[user_id]:
        await ctx.send(f"{member.mention} не в ваших друзьях")
        return

    friends_data[user_id].remove(target_id)
    save_friends(friends_data)
    await ctx.send(f"{ctx.author.mention} удалил {member.mention} из друзей")


@bot.command()
async def friends(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    friends_data = load_friends()
    user_id = str(member.id)

    if user_id not in friends_data or not friends_data[user_id]:
        await ctx.send(f"У {member.mention} нет друзей")
        return

    friend_list = []
    for friend_id in friends_data[user_id]:
        friend = await bot.fetch_user(int(friend_id))
        friend_list.append(friend.name)

    embed = discord.Embed(title=f"Друзья {member.name}", color=0x00ff00)
    embed.add_field(name="Список друзей", value=", ".join(friend_list))
    await ctx.send(embed=embed)


@bot.command()
async def tasks(ctx):
    tasks_data = load_tasks()
    user_id = str(ctx.author.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id not in tasks_data or tasks_data[user_id].get("date") != today:
        tasks_data[user_id] = {
            "date": today,
            "messages": 0,
            "casino_wins": 0,
            "voice_minutes": 0,
            "daily_done": False
        }
        save_tasks(tasks_data)

    user_tasks = tasks_data[user_id]

    embed = discord.Embed(title="Ежедневные задания", color=0x00ff00)
    embed.add_field(name="Написать 10 сообщений", value=f"Выполнено: {user_tasks['messages']}/10", inline=False)
    embed.add_field(name="Выиграть в казино 3 раза", value=f"Выполнено: {user_tasks['casino_wins']}/3", inline=False)
    embed.add_field(name="Получить ежедневный бонус",
                    value="Выполнено: Да" if user_tasks['daily_done'] else "Выполнено: Нет", inline=False)
    embed.set_footer(text="Награда за полное выполнение: 30 опыта")

    await ctx.send(embed=embed)


@bot.command()
async def claim(ctx):
    tasks_data = load_tasks()
    user_id = str(ctx.author.id)
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id not in tasks_data or tasks_data[user_id].get("date") != today:
        await ctx.send("Сначала выполните задания. Используйте !tasks")
        return

    user_tasks = tasks_data[user_id]

    if user_tasks["messages"] >= 10 and user_tasks["casino_wins"] >= 3 and user_tasks["daily_done"]:
        if user_tasks.get("claimed", False):
            await ctx.send("Вы уже получили награду сегодня")
            return

        data = load_data()
        if user_id not in data:
            data[user_id] = {"xp": 0, "level": 0, "total_xp": 0}

        data[user_id]["total_xp"] += 30
        data[user_id]["xp"] += 30

        while data[user_id]["xp"] >= (data[user_id]["level"] + 1) * 100:
            data[user_id]["xp"] -= (data[user_id]["level"] + 1) * 100
            data[user_id]["level"] += 1
            await ctx.send(f"{ctx.author.mention} повысился до {data[user_id]['level']} уровня!")

        save_data(data)

        user_tasks["claimed"] = True
        save_tasks(tasks_data)

        await ctx.send(f"{ctx.author.mention} выполнил все задания и получил 30 опыта!")
    else:
        await ctx.send("Вы выполнили не все задания. Используйте !tasks чтобы проверить прогресс")


bot.run(TOKEN)
