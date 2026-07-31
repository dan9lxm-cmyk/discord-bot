import os
import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import asyncio
import random
import logging
import sys
import traceback

# Настройка логирования ошибок
logging.basicConfig(level=logging.INFO)

# ==================== ГЛОБАЛЬНЫЙ ОБРАБОТЧИК ОШИБОК ====================

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Обработка ошибок команд"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"❌ У вас нет прав для этой команды!")
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Неправильный аргумент: {error}")
            return
        
        error_msg = f"Ошибка в команде {ctx.command}: {error}\n{traceback.format_exc()}"
        logging.error(error_msg)
        
        await ctx.send(f"❌ Произошла ошибка. Администраторы уведомлены.")
        
        log_channel = self.bot.get_channel(1531831553162874961)
        if log_channel:
            try:
                embed = discord.Embed(
                    title="❌ Ошибка",
                    description=f"```py\n{error_msg[:1900]}\n```",
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed)
            except:
                pass

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Глобальный обработчик ошибок"""
        error_msg = f"Ошибка в событии {event}:\n{traceback.format_exc()}"
        logging.error(error_msg)
        
        log_channel = self.bot.get_channel(1531831553162874961)
        if log_channel:
            try:
                embed = discord.Embed(
                    title="⚠️ Критическая ошибка",
                    description=f"```py\n{error_msg[:1900]}\n```",
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed)
            except:
                pass


# ==================== ПЕРЕХВАТ КРИТИЧЕСКИХ ОШИБОК ====================

def setup_exception_handler():
    """Настройка глобального перехвата исключений"""
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"Необработанное исключение: {exc_type.__name__}: {exc_value}\n{''.join(traceback.format_tb(exc_traceback))}"
        logging.critical(error_msg)
        print(f"💀 КРИТИЧЕСКАЯ ОШИБКА: {error_msg}")
        sys.exit(1)
    
    sys.excepthook = global_exception_handler

# Включаем обработчик
setup_exception_handler()


# ==================== НАСТРОЙКИ БОТА ====================

# Настройки бота
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Добавляем обработчик ошибок
bot.add_cog(ErrorHandler(bot))

# ID канала для приветствия (ОБЯЗАТЕЛЬНО ЗАМЕНИТЕ!)
WELCOME_CHANNEL_ID = 1532715863717707848
ROLE_CHANGE_CHANNEL_ID = 1532778968841851022

# НАЗВАНИЕ РОЛИ ДЛЯ НОВИЧКОВ (можно изменить)
NEWBIE_ROLE_NAME = "Новичок"

# Роль, которая выдаётся после регистрации (даёт доступ к серверу)
MAIN_ROLE_NAME = "Китайский младший"

# Эмодзи
EMOJIS = {
    'welcome': '👋',
    'gender': '👤',
    'age': '🎂',
    'games': '🎮',
    'male': '👨',
    'female': '👩',
    'complete': '✅',
    'star': '⭐',
    'sparkles': '✨',
    'crown': '👑',
    'party': '🎉',
    'heart': '💖',
    'fire': '🔥',
    'rainbow': '🌈',
    'rocket': '🚀',
    'confetti': '🎊'
}

# Цвета для гендерных ролей
GENDER_COLORS = {
    'male': discord.Color.blue(),
    'female': discord.Color.magenta()
}

# Цвета для возрастных ролей
AGE_COLORS = {
    'Меньше 16 лет': discord.Color.from_rgb(255, 182, 193),
    '16-17 лет': discord.Color.from_rgb(144, 238, 144),
    '18-24 лет': discord.Color.from_rgb(60, 179, 113),
    '25-29 лет': discord.Color.from_rgb(255, 165, 0),
    '30+ лет': discord.Color.from_rgb(218, 165, 32)
}

# Цвета для игровых ролей
GAME_COLORS = [
    discord.Color.from_rgb(255, 99, 71),
    discord.Color.from_rgb(65, 105, 225),
    discord.Color.from_rgb(50, 205, 50),
    discord.Color.from_rgb(255, 215, 0),
    discord.Color.from_rgb(138, 43, 226),
    discord.Color.from_rgb(255, 105, 180),
    discord.Color.from_rgb(0, 206, 209),
    discord.Color.from_rgb(220, 20, 60),
    discord.Color.from_rgb(123, 104, 238),
    discord.Color.from_rgb(255, 140, 0),
    discord.Color.from_rgb(154, 205, 50),
    discord.Color.from_rgb(186, 85, 211)
]

# ==================== ФУНКЦИИ РАБОТЫ С РОЛЯМИ ====================
# (тут идёт весь ваш код с функциями, классами, командами и событиями)

# ==================== ЗАПУСК ====================
# (в самом конце)

# ==================== ФУНКЦИИ РАБОТЫ С РОЛЯМИ ====================

async def find_or_create_role(guild, role_name, color):
    """Находит существующую роль или создаёт новую"""
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        return role
    
    for r in guild.roles:
        if role_name.lower() in r.name.lower():
            return r
    
    try:
        new_role = await guild.create_role(
            name=role_name,
            color=color,
            mentionable=True,
            reason="Автоматическое создание роли ботом"
        )
        print(f"✅ Создана роль: {new_role.name} (цвет: {color})")
        return new_role
    except Exception as e:
        print(f"❌ Ошибка создания роли {role_name}: {e}")
        return None


async def assign_newbie_role(member):
    """Выдаёт роль новичка"""
    try:
        role = await find_or_create_role(member.guild, NEWBIE_ROLE_NAME, discord.Color.light_gray())
        if role and role not in member.roles:
            await member.add_roles(role)
            print(f"✅ Выдана роль новичка: {member.name}")
            return True
    except Exception as e:
        print(f"❌ Ошибка выдачи роли новичка: {e}")
    return False


async def remove_newbie_role(member):
    """Удаляет роль новичка после регистрации"""
    try:
        role = discord.utils.get(member.guild.roles, name=NEWBIE_ROLE_NAME)
        if role and role in member.roles:
            await member.remove_roles(role)
            print(f"✅ Удалена роль новичка у {member.name}")
            return True
    except Exception as e:
        print(f"❌ Ошибка удаления роли новичка: {e}")
    return False


async def assign_main_role(member):
    """Выдаёт основную роль после регистрации. Ищет по разным вариациям названия."""
    try:
        # Все возможные вариации названия роли
        role_variations = [
            "Китайский младший",
            "китайский младший",
            "Китайский Младший",
            "китайский Младший",
            "Китайский младшый",
            "китайский младшый",
            "Младший китайский",
            "младший китайский",
            "Китаец",
            "китаец",
            "China",
            "china"
        ]
        
        # Ищем роль по всем вариациям
        found_role = None
        for variation in role_variations:
            role = discord.utils.get(member.guild.roles, name=variation)
            if role:
                found_role = role
                print(f"🔍 Найдена роль: {role.name} (по запросу: {variation})")
                break
        
        # Если роль не найдена - создаём
        if not found_role:
            print(f"🔧 Роль '{MAIN_ROLE_NAME}' не найдена, создаю...")
            
            # Создаём роль с базовыми правами
            permissions = discord.Permissions(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                connect=True,
                speak=True,
                view_channel=True,
                add_reactions=True,
                embed_links=True,
                attach_files=True,
                external_emojis=True
            )
            
            found_role = await member.guild.create_role(
                name=MAIN_ROLE_NAME,
                color=discord.Color.blue(),
                permissions=permissions,
                mentionable=True,
                reason="Автоматическое создание основной роли ботом"
            )
            print(f"✅ Создана основная роль: {found_role.name} с правами на просмотр")
        
        # Выдаём роль
        if found_role and found_role not in member.roles:
            await member.add_roles(found_role)
            print(f"✅ Выдана основная роль: {found_role.name} -> {member.name}")
            return True
        else:
            print(f"ℹ️ Роль уже есть у {member.name}")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка выдачи основной роли: {e}")
        return False


async def assign_main_role_for_guild(guild):
    """Создаёт основную роль на сервере при запуске"""
    try:
        # Все возможные вариации названия роли
        role_variations = [
            "Китайский младший",
            "китайский младший",
            "Китайский Младший",
            "китайский Младший",
            "Китайский младшый",
            "китайский младшый",
            "Младший китайский",
            "младший китайский",
            "Китаец",
            "китаец",
            "China",
            "china"
        ]
        
        # Ищем роль по всем вариациям
        found_role = None
        for variation in role_variations:
            role = discord.utils.get(guild.roles, name=variation)
            if role:
                found_role = role
                print(f"🔍 Найдена роль на сервере {guild.name}: {role.name}")
                break
        
        if not found_role:
            permissions = discord.Permissions(
                read_messages=True,
                send_messages=True,
                read_message_history=True,
                connect=True,
                speak=True,
                view_channel=True,
                add_reactions=True,
                embed_links=True,
                attach_files=True,
                external_emojis=True
            )
            
            found_role = await guild.create_role(
                name=MAIN_ROLE_NAME,
                color=discord.Color.blue(),
                permissions=permissions,
                mentionable=True,
                reason="Автоматическое создание основной роли ботом"
            )
            print(f"✅ Создана основная роль: {found_role.name} на сервере {guild.name}")
        else:
            print(f"ℹ️ Роль уже существует на сервере {guild.name}")
            
    except Exception as e:
        print(f"❌ Ошибка создания основной роли: {e}")


async def assign_gender_role(member, gender):
    """Назначает гендерную роль"""
    if not gender:
        print("❌ Пол не указан, пропускаем")
        return None
        
    if gender == 'male':
        role_name = 'Мужчина'
        color = GENDER_COLORS['male']
        opposite = ['Женщина', 'Ж', 'Жен', 'Female', 'Woman', 'Девушка', 'Тянка', 'Тян', 'Тяночка']
    else:
        role_name = 'Женщина'
        color = GENDER_COLORS['female']
        opposite = ['Мужчина', 'М', 'Муж', 'Male', 'Man', 'Парень']
    
    try:
        role = await find_or_create_role(member.guild, role_name, color)
        if not role:
            print("❌ Не удалось найти/создать гендерную роль")
            return None
        
        for opp_name in opposite:
            opp_role = discord.utils.get(member.guild.roles, name=opp_name)
            if opp_role and opp_role in member.roles:
                await member.remove_roles(opp_role)
        
        if role not in member.roles:
            await member.add_roles(role)
            print(f"✅ Назначена роль: {role.name} -> {member.name}")
        else:
            print(f"ℹ️ Роль {role.name} уже есть у {member.name}")
        
        return role
        
    except Exception as e:
        print(f"❌ Ошибка назначения гендерной роли: {e}")
        return None


async def assign_age_role(member, age):
    """Назначает возрастную роль"""
    if not age:
        print("❌ Возраст не указан, пропускаем")
        return None
        
    role_name = age
    color = AGE_COLORS.get(age, discord.Color.default())
    
    try:
        role = await find_or_create_role(member.guild, role_name, color)
        if not role:
            print("❌ Не удалось найти/создать возрастную роль")
            return None
        
        for age_key in AGE_COLORS.keys():
            if age_key != age:
                old_role = discord.utils.get(member.guild.roles, name=age_key)
                if old_role and old_role in member.roles:
                    await member.remove_roles(old_role)
        
        if role not in member.roles:
            await member.add_roles(role)
            print(f"✅ Назначена роль: {role.name} -> {member.name}")
        else:
            print(f"ℹ️ Роль {role.name} уже есть у {member.name}")
        
        return role
        
    except Exception as e:
        print(f"❌ Ошибка назначения возрастной роли: {e}")
        return None


async def assign_game_roles(member, games):
    """Назначает игровые роли"""
    if not games:
        print("❌ Игры не выбраны, пропускаем")
        return []
        
    assigned = []
    all_games = ['Dota 2', 'CS2', 'Valorant', 'LoL', 'Apex', 'Overwatch', 
                 'Fortnite', 'Minecraft', 'PUBG', 'WoW', 'CoD', 'Roblox']
    
    for game in all_games:
        if game not in games:
            old_role = discord.utils.get(member.guild.roles, name=game)
            if old_role and old_role in member.roles:
                await member.remove_roles(old_role)
    
    used_colors = set()
    for role in member.guild.roles:
        if role.color != discord.Color.default():
            used_colors.add(role.color.value)
    
    for i, game in enumerate(games):
        try:
            available = [c for c in GAME_COLORS if c.value not in used_colors]
            if available:
                color = available[0]
            else:
                color = discord.Color.from_rgb(
                    random.randint(50, 255),
                    random.randint(50, 255),
                    random.randint(50, 255)
                )
            used_colors.add(color.value)
            
            role = await find_or_create_role(member.guild, game, color)
            if role and role not in member.roles:
                await member.add_roles(role)
                assigned.append(role)
                print(f"✅ Назначена роль: {role.name} -> {member.name}")
                
        except Exception as e:
            print(f"❌ Ошибка назначения роли {game}: {e}")
    
    return assigned


# ==================== КЛАССЫ ИНТЕРФЕЙСА ====================

class ApplyView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='📝 Пройти регистрацию', style=discord.ButtonStyle.success, custom_id='apply_button')
    async def apply_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        try:
            member = await interaction.guild.fetch_member(interaction.user.id)
            user_data = {'member': member, 'guild': interaction.guild}
            
            # Проверяем, есть ли уже роль новичка
            newbie_role = discord.utils.get(member.guild.roles, name=NEWBIE_ROLE_NAME)
            if newbie_role not in member.roles:
                await interaction.followup.send("❌ У вас нет роли новичка! Обратитесь к администратору.", ephemeral=True)
                return
            
            welcome_embed = discord.Embed(
                title=f"{EMOJIS['welcome']} Добро пожаловать на сервер **{interaction.guild.name}**!",
                description=f"{EMOJIS['sparkles']} Привет, {interaction.user.name}! Мы рады видеть тебя здесь!\n\n"
                           f"{EMOJIS['star']} Давай познакомимся поближе!",
                color=discord.Color.blue()
            )
            
            gender_embed = discord.Embed(
                title=f"{EMOJIS['gender']} Вопрос 1 из 3: Выберите свой пол",
                description=f"{EMOJIS['star']} Кто вы?",
                color=discord.Color.blue()
            )
            gender_embed.set_footer(text="Нажмите на одну из кнопок ниже")
            
            view = GenderView(user_data)
            await interaction.user.send(embed=welcome_embed)
            await interaction.user.send(embed=gender_embed, view=view)
            await interaction.followup.send(f"{EMOJIS['rocket']} Проверь личные сообщения!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Откройте личные сообщения в настройках Discord!", ephemeral=True)
        except Exception as e:
            print(f"Ошибка в apply_button: {e}")
            await interaction.followup.send("❌ Произошла ошибка. Попробуйте позже.", ephemeral=True)


class GenderView(View):
    def __init__(self, user_data):
        super().__init__(timeout=300)
        self.user_data = user_data
        
    @discord.ui.button(label='Я мужчина', style=discord.ButtonStyle.primary, emoji='👨')
    async def male_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.user_data['gender'] = 'male'
        await interaction.followup.send(f"{EMOJIS['male']} Отлично! Вы выбрали: **Мужчина**", ephemeral=True)
        await show_age_selection(interaction, self.user_data)
        self.stop()
        
    @discord.ui.button(label='Я женщина', style=discord.ButtonStyle.primary, emoji='👩')
    async def female_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        self.user_data['gender'] = 'female'
        await interaction.followup.send(f"{EMOJIS['female']} Прекрасно! Вы выбрали: **Женщина**", ephemeral=True)
        await show_age_selection(interaction, self.user_data)
        self.stop()


class AgeView(View):
    def __init__(self, user_data):
        super().__init__(timeout=300)
        self.user_data = user_data
        
        ages = [
            ('🍼 Меньше 16 лет', '🍼'),
            ('🌱 16-17 лет', '🌱'),
            ('🌿 18-24 лет', '🌿'),
            ('🌳 25-29 лет', '🌳'),
            ('🍂 30+ лет', '🍂')
        ]
        
        for age, emoji in ages:
            button = Button(
                label=age,
                style=discord.ButtonStyle.primary,
                emoji=emoji
            )
            button.callback = self.create_age_callback(age)
            self.add_item(button)
    
    def create_age_callback(self, age):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            clean_age = age.replace('🍼 ', '').replace('🌱 ', '').replace('🌿 ', '').replace('🌳 ', '').replace('🍂 ', '')
            self.user_data['age'] = clean_age
            await interaction.followup.send(f"{EMOJIS['age']} Принято! Ваш возраст: **{clean_age}**", ephemeral=True)
            await show_games_selection(interaction, self.user_data)
            self.stop()
        return callback


class GamesSelect(Select):
    def __init__(self, user_data):
        self.user_data = user_data
        
        options = [
            discord.SelectOption(label='Dota 2', emoji='⚔️', value='Dota 2'),
            discord.SelectOption(label='CS2', emoji='🎯', value='CS2'),
            discord.SelectOption(label='Valorant', emoji='💣', value='Valorant'),
            discord.SelectOption(label='LoL', emoji='🏰', value='LoL'),
            discord.SelectOption(label='Apex', emoji='🦾', value='Apex'),
            discord.SelectOption(label='Overwatch', emoji='🦸', value='Overwatch'),
            discord.SelectOption(label='Fortnite', emoji='🏗️', value='Fortnite'),
            discord.SelectOption(label='Minecraft', emoji='⛏️', value='Minecraft'),
            discord.SelectOption(label='PUBG', emoji='🍗', value='PUBG'),
            discord.SelectOption(label='WoW', emoji='🐉', value='WoW'),
            discord.SelectOption(label='CoD', emoji='💀', value='CoD'),
            discord.SelectOption(label='Roblox', emoji='🎲', value='Roblox')
        ]
        
        super().__init__(
            placeholder='🎮 Выберите ваши любимые игры...',
            min_values=1,
            max_values=len(options),
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.user_data['games'] = self.values
        games_list = '\n'.join([f'• {game}' for game in self.values])
        await interaction.followup.send(f"{EMOJIS['games']} Вы выбрали игры:\n{games_list}", ephemeral=True)
        await complete_registration(interaction, self.user_data)
        self.view.stop()


class GamesView(View):
    def __init__(self, user_data):
        super().__init__(timeout=300)
        self.user_data = user_data
        self.add_item(GamesSelect(user_data))


class ChangeGamesView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='🎮 Сменить игры', style=discord.ButtonStyle.primary, custom_id='change_games')
    async def change_games(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        try:
            member = await interaction.guild.fetch_member(interaction.user.id)
            user_data = {'member': member, 'guild': interaction.guild}
            
            embed = discord.Embed(
                title=f"{EMOJIS['games']} Выберите ваши любимые игры",
                description=f"{EMOJIS['sparkles']} Во что вы сейчас играете?\nВы можете выбрать несколько вариантов!",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Старые игровые роли будут заменены")
            
            view = GamesView(user_data)
            await interaction.user.send(embed=embed, view=view)
            await interaction.followup.send(f"{EMOJIS['rocket']} Проверь личные сообщения!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Откройте личные сообщения!", ephemeral=True)
    
    @discord.ui.button(label='👤 Указать пол (если нет)', style=discord.ButtonStyle.secondary, custom_id='add_gender')
    async def add_gender(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        member = await interaction.guild.fetch_member(interaction.user.id)
        
        # Проверяем, есть ли уже гендерная роль
        has_gender = False
        for role in member.roles:
            if role.name.lower() in ['мужчина', 'женщина', 'м', 'ж', 'male', 'female', 'man', 'woman', 'парень', 'девушка', 'тянка', 'тян']:
                has_gender = True
                break
        
        if has_gender:
            await interaction.followup.send("❌ У вас уже указан пол. Обратитесь к администратору для смены.", ephemeral=True)
            return
        
        try:
            user_data = {'member': member, 'guild': interaction.guild}
            
            embed = discord.Embed(
                title=f"{EMOJIS['gender']} Выберите свой пол",
                description=f"{EMOJIS['star']} Кто вы?",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Пол можно указать только один раз")
            
            view = GenderView(user_data)
            await interaction.user.send(embed=embed, view=view)
            await interaction.followup.send(f"{EMOJIS['rocket']} Проверь личные сообщения!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Откройте личные сообщения!", ephemeral=True)
    
    @discord.ui.button(label='🎂 Указать возраст (если нет)', style=discord.ButtonStyle.secondary, custom_id='add_age')
    async def add_age(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        member = await interaction.guild.fetch_member(interaction.user.id)
        
        # Проверяем, есть ли уже возрастная роль
        has_age = False
        for age_key in AGE_COLORS.keys():
            if discord.utils.get(member.roles, name=age_key):
                has_age = True
                break
        
        if has_age:
            await interaction.followup.send("❌ У вас уже указан возраст. Обратитесь к администратору для смены.", ephemeral=True)
            return
        
        try:
            user_data = {'member': member, 'guild': interaction.guild}
            
            embed = discord.Embed(
                title=f"{EMOJIS['age']} Выберите ваш возраст",
                description=f"{EMOJIS['star']} К какой возрастной категории вы относитесь?",
                color=discord.Color.green()
            )
            embed.set_footer(text="Возраст можно указать только один раз")
            
            view = AgeView(user_data)
            await interaction.user.send(embed=embed, view=view)
            await interaction.followup.send(f"{EMOJIS['rocket']} Проверь личные сообщения!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Откройте личные сообщения!", ephemeral=True)


# ==================== ФУНКЦИИ ПОКАЗА ВОПРОСОВ ====================

async def show_age_selection(interaction: discord.Interaction, user_data):
    embed = discord.Embed(
        title=f"{EMOJIS['age']} Вопрос 2 из 3: Выберите ваш возраст",
        description=f"{EMOJIS['star']} К какой возрастной категории вы относитесь?",
        color=discord.Color.green()
    )
    embed.set_footer(text="Выберите один из вариантов ниже")
    
    view = AgeView(user_data)
    await interaction.user.send(embed=embed, view=view)


async def show_games_selection(interaction: discord.Interaction, user_data):
    embed = discord.Embed(
        title=f"{EMOJIS['games']} Вопрос 3 из 3: Выберите ваши любимые игры",
        description=f"{EMOJIS['sparkles']} Во что вы любите играть?\nВы можете выбрать несколько вариантов!",
        color=discord.Color.purple()
    )
    embed.set_footer(text="Выберите одну или несколько игр из списка")
    
    view = GamesView(user_data)
    await interaction.user.send(embed=embed, view=view)


# ==================== ЗАВЕРШЕНИЕ РЕГИСТРАЦИИ ====================

async def complete_registration(interaction: discord.Interaction, user_data):
    """Финализирует регистрацию и выдаёт роли"""
    member = user_data['member']
    
    complete_embed = discord.Embed(
        title=f"{EMOJIS['complete']} Регистрация завершена!",
        description=f"{EMOJIS['party']} Поздравляем, {member.name}!",
        color=discord.Color.teal()
    )
    
    if user_data.get('gender') == 'male':
        gender_display = "👨 Мужчина"
    elif user_data.get('gender') == 'female':
        gender_display = "👩 Женщина"
    else:
        gender_display = "❓ Не указан"
    
    age_value = user_data.get('age', '❓ Не указан')
    
    games = user_data.get('games', [])
    if games:
        games_display = '\n'.join([f'{EMOJIS["star"]} {game}' for game in games])
    else:
        games_display = "❓ Не выбраны"
    
    complete_embed.add_field(name=f"{EMOJIS['gender']} Пол", value=gender_display, inline=True)
    complete_embed.add_field(name=f"{EMOJIS['age']} Возраст", value=age_value, inline=True)
    complete_embed.add_field(name=f"{EMOJIS['games']} Игры", value=games_display, inline=False)
    complete_embed.set_thumbnail(url=member.display_avatar.url)
    
    await interaction.user.send(embed=complete_embed)
    
    print(f"\n📋 Назначение ролей для {member.name}:")
    
    gender_role = None
    if user_data.get('gender'):
        gender_role = await assign_gender_role(member, user_data['gender'])
    
    age_role = None
    if user_data.get('age'):
        age_role = await assign_age_role(member, user_data['age'])
    
    game_roles = []
    if user_data.get('games'):
        game_roles = await assign_game_roles(member, user_data['games'])
    
    # Удаляем роль новичка
    await remove_newbie_role(member)
    
    # Выдаём основную роль
    await assign_main_role(member)
    
    await asyncio.sleep(1)
    
    final_embed = discord.Embed(
        title=f"{EMOJIS['crown']} Добро пожаловать в семью!",
        description=f"{EMOJIS['rainbow']} {member.mention}, теперь ты полноценный участник сервера!\n\n"
                   f"{EMOJIS['heart']} Вот твои роли:",
        color=discord.Color.gold()
    )
    
    roles_list = []
    if gender_role:
        roles_list.append(f"{EMOJIS['gender']} {gender_role.mention}")
    if age_role:
        roles_list.append(f"{EMOJIS['age']} {age_role.mention}")
    if game_roles:
        game_mentions = ' '.join([r.mention for r in game_roles])
        roles_list.append(f"{EMOJIS['games']} {game_mentions}")
    
    if roles_list:
        final_embed.add_field(name="📋 Назначенные роли", value='\n'.join(roles_list), inline=False)
    else:
        final_embed.add_field(name="📋 Назначенные роли", value="❌ Роли не были назначены", inline=False)
    
    final_embed.add_field(name=f"{EMOJIS['fire']} Начни общение!", 
                         value="Заходи в голосовые каналы и текстовые чаты!\nРасскажи о себе в общем чате.",
                         inline=False)
    final_embed.set_footer(text=f"{EMOJIS['confetti']} Мы рады, что ты с нами!")
    
    await interaction.user.send(embed=final_embed)
    
    # Уведомление в канал логов
    channel = bot.get_channel(1531831553162874961)
    if channel:
        welcome_embed = discord.Embed(
            description=f"{EMOJIS['party']} {member.mention} только что прошёл регистрацию!\n"
                    f"{EMOJIS['sparkles']} Поприветствуем нового участника!",
            color=discord.Color.green()
        )
        await channel.send(embed=welcome_embed)


# ==================== СОБЫТИЯ БОТА ====================

@bot.event
async def on_ready():
    print(f'{EMOJIS["sparkles"]} Бот {bot.user} успешно запущен!')
    print(f'Подключен к {len(bot.guilds)} серверам')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="За новыми участниками 👀"
        ),
        status=discord.Status.online
    )
    
    for guild in bot.guilds:
        # Создаём роль новичка
        await find_or_create_role(guild, NEWBIE_ROLE_NAME, discord.Color.light_gray())
        
        # Создаём основную роль
        await assign_main_role_for_guild(guild)
        
        # ===== ПРИВЕТСТВЕННЫЙ КАНАЛ =====
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            try:
                async for message in channel.history(limit=50):
                    if message.author == bot.user:
                        try:
                            await message.delete()
                        except:
                            pass
                    await asyncio.sleep(0.5)
            except:
                pass
            
            embed = discord.Embed(
                title=f"{EMOJIS['welcome']} Добро пожаловать на сервер **{guild.name}**!",
                description=f"{EMOJIS['sparkles']} Чтобы получить доступ ко всем каналам,\n"
                           f"нажмите на кнопку ниже для регистрации!\n\n"
                           f"{EMOJIS['star']} Это займёт всего пару минут.\n\n"
                           f"⚠️ **У вас есть роль {NEWBIE_ROLE_NAME}**\n"
                           f"После регистрации она будет автоматически удалена.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.set_footer(text="Регистрация через личные сообщения")
            
            view = ApplyView()
            await channel.send(embed=embed, view=view)
    
    # ===== КАНАЛ ДЛЯ СМЕНЫ РОЛЕЙ =====
    role_channel = bot.get_channel(ROLE_CHANGE_CHANNEL_ID)
    if role_channel:
        try:
            async for message in role_channel.history(limit=50):
                if message.author == bot.user:
                    try:
                        await message.delete()
                    except:
                        pass
                await asyncio.sleep(0.5)
        except:
            pass
        
        embed = discord.Embed(
            title="🔄 Смена игровых ролей",
            description=f"{EMOJIS['sparkles']} Здесь вы можете изменить свои игровые роли\n"
                       f"или указать пол/возраст, если ещё не указали.\n\n"
                       f"🎮 **Сменить игры** — заменить игровые роли\n"
                       f"👤 **Указать пол** — только если ещё нет\n"
                       f"🎂 **Указать возраст** — только если ещё нет",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Нажмите на кнопку ниже")
        
        view = ChangeGamesView()
        await role_channel.send(embed=embed, view=view)


@bot.event
async def on_member_join(member):
    """При входе участника выдаём роль новичка"""
    # Проверяем, есть ли уже роли (кроме @everyone)
    if len(member.roles) > 1:
        print(f"ℹ️ {member.name} уже имеет роли, пропускаем")
        return
    
    # Выдаём роль новичка
    await assign_newbie_role(member)
    print(f"📥 {member.name} получил роль {NEWBIE_ROLE_NAME}")


# ==================== КОМАНДЫ ====================

@bot.command(name='setup')
@commands.has_permissions(administrator=True)
async def setup_welcome(ctx):
    channel = ctx.guild.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Укажите правильный ID канала в коде!")
        return
    
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user:
                try:
                    await message.delete()
                except:
                    pass
            await asyncio.sleep(0.5)
    except:
        pass
    
    embed = discord.Embed(
        title=f"{EMOJIS['welcome']} Добро пожаловать на сервер **{ctx.guild.name}**!",
        description=f"{EMOJIS['sparkles']} Чтобы получить доступ ко всем каналам,\n"
                   f"нажмите на кнопку ниже для регистрации!\n\n"
                   f"{EMOJIS['star']} Это займёт всего пару минут.\n\n"
                   f"⚠️ **У вас есть роль {NEWBIE_ROLE_NAME}**\n"
                   f"После регистрации она будет автоматически удалена.",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    embed.set_footer(text="Регистрация через личные сообщения")
    
    view = ApplyView()
    await channel.send(embed=embed, view=view)
    await ctx.send(f"{EMOJIS['complete']} Приветственное сообщение установлено!")


@bot.command(name='setup_roles')
@commands.has_permissions(administrator=True)
async def setup_role_channel(ctx):
    channel = bot.get_channel(ROLE_CHANGE_CHANNEL_ID)
    if not channel:
        await ctx.send("❌ Неверный ID канала для смены ролей!")
        return
    
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user:
                try:
                    await message.delete()
                except:
                    pass
            await asyncio.sleep(0.5)
    except:
        pass
    
    embed = discord.Embed(
        title="🔄 Смена игровых ролей",
        description=f"{EMOJIS['sparkles']} Здесь вы можете изменить свои игровые роли\n"
                   f"или указать пол/возраст, если ещё не указали.\n\n"
                   f"🎮 **Сменить игры** — заменить игровые роли\n"
                   f"👤 **Указать пол** — только если ещё нет\n"
                   f"🎂 **Указать возраст** — только если ещё нет",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Нажмите на кнопку ниже")
    
    view = ChangeGamesView()
    await channel.send(embed=embed, view=view)
    await ctx.send(f"{EMOJIS['complete']} Сообщение для смены ролей установлено!")


@bot.command(name='test')
async def test_registration(ctx):
    try:
        member = await ctx.guild.fetch_member(ctx.author.id)
        user_data = {'member': member, 'guild': ctx.guild}
        
        welcome_embed = discord.Embed(
            title=f"{EMOJIS['welcome']} Тестовая регистрация",
            description=f"{EMOJIS['sparkles']} Давай протестируем процесс регистрации!",
            color=discord.Color.blue()
        )
        
        gender_embed = discord.Embed(
            title=f"{EMOJIS['gender']} Вопрос 1 из 3: Выберите свой пол",
            description=f"{EMOJIS['star']} Кто вы?",
            color=discord.Color.blue()
        )
        gender_embed.set_footer(text="Нажмите на одну из кнопок ниже")
        
        view = GenderView(user_data)
        await ctx.author.send(embed=welcome_embed)
        await ctx.author.send(embed=gender_embed, view=view)
        await ctx.send(f"{EMOJIS['rocket']} Проверь личные сообщения!")
        
    except discord.Forbidden:
        await ctx.send("❌ Открой личные сообщения в настройках Discord!")
    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")


@bot.command(name='clear_all')
@commands.has_permissions(administrator=True)
async def clear_all(ctx):
    """Удаляет ВСЕ сообщения бота в канале"""
    deleted = 0
    async for message in ctx.channel.history(limit=1000):
        if message.author == bot.user:
            try:
                await message.delete()
                deleted += 1
                await asyncio.sleep(0.5)
            except:
                pass
    await ctx.send(f"✅ Удалено {deleted} сообщений бота!", delete_after=5)


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')  # ЗАМЕНИТЕ НА ТОКЕН БОТА
    bot.run(TOKEN)
