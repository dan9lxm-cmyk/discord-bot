import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import asyncio
import random
import logging
import sys
import traceback
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования ошибок
logging.basicConfig(level=logging.INFO)

# ==================== ПЕРЕХВАТ КРИТИЧЕСКИХ ОШИБОК ====================

def setup_exception_handler():
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"Необработанное исключение: {exc_type.__name__}: {exc_value}\n{''.join(traceback.format_tb(exc_traceback))}"
        logging.critical(error_msg)
        print(f"💀 КРИТИЧЕСКАЯ ОШИБКА: {error_msg}")
        sys.exit(1)
    
    sys.excepthook = global_exception_handler

setup_exception_handler()

# ==================== НАСТРОЙКИ БОТА ====================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CHANNEL_NAME = "🏯・ворота・небес・天门・тяньмэнь"
ROLE_CHANGE_CHANNEL_NAME = "✒️・изменение・ролей"
DATING_CHANNEL_NAME = "🌙・свидание・под・луной・月约・юэюэ"
LOG_CHANNEL_ID = int(os.environ.get('LOG_CHANNEL_ID', 1531831553162874961))
ARCHIVE_CHANNEL_NAME = "📜・архив・логи・"
NEWBIE_ROLE_NAME = "Новичок"
MAIN_ROLE_NAME = "🌸・Странник"

APPLICATIONS_FILE = "applications_data.json"
SETTINGS_FILE = "bot_settings.json"
ACTIVE_CHATS_FILE = "active_chats.json"
BLOCKED_USERS_FILE = "blocked_users.json"
TEMP_CHANNELS_FILE = "temp_channels.json"
CHAT_HISTORY_FILE = "chat_history.json"

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ====================

def load_blocked_users():
    try:
        if os.path.exists(BLOCKED_USERS_FILE):
            with open(BLOCKED_USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"blocked": {}}
    except Exception as e:
        print(f"❌ Ошибка загрузки блокировок: {e}")
        return {"blocked": {}}

def save_blocked_users(data):
    try:
        with open(BLOCKED_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения блокировок: {e}")
        return False

def block_user(blocker_id, blocked_id):
    data = load_blocked_users()
    blocker_id = str(blocker_id)
    blocked_id = str(blocked_id)
    
    if blocker_id not in data["blocked"]:
        data["blocked"][blocker_id] = []
    
    if blocked_id not in data["blocked"][blocker_id]:
        data["blocked"][blocker_id].append(blocked_id)
        save_blocked_users(data)
        return True
    return False

def unblock_user(blocker_id, blocked_id):
    data = load_blocked_users()
    blocker_id = str(blocker_id)
    blocked_id = str(blocked_id)
    
    if blocker_id in data["blocked"] and blocked_id in data["blocked"][blocker_id]:
        data["blocked"][blocker_id].remove(blocked_id)
        save_blocked_users(data)
        return True
    return False

def is_user_blocked(blocker_id, blocked_id):
    data = load_blocked_users()
    blocker_id = str(blocker_id)
    blocked_id = str(blocked_id)
    
    if blocker_id in data["blocked"]:
        return blocked_id in data["blocked"][blocker_id]
    return False

def load_temp_channels():
    try:
        if os.path.exists(TEMP_CHANNELS_FILE):
            with open(TEMP_CHANNELS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"channels": {}}
    except Exception as e:
        print(f"❌ Ошибка загрузки временных каналов: {e}")
        return {"channels": {}}

def save_temp_channels(data):
    try:
        with open(TEMP_CHANNELS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения временных каналов: {e}")
        return False

def add_temp_channel(channel_id, application_id, user1_id, user2_id, is_anonymous=False):
    data = load_temp_channels()
    data["channels"][str(channel_id)] = {
        "application_id": str(application_id),
        "user1_id": str(user1_id),
        "user2_id": str(user2_id),
        "created_at": datetime.now().isoformat(),
        "is_active": True,
        "is_anonymous": is_anonymous
    }
    save_temp_channels(data)
    return True

def remove_temp_channel(channel_id):
    data = load_temp_channels()
    if str(channel_id) in data["channels"]:
        data["channels"][str(channel_id)]["is_active"] = False
        save_temp_channels(data)
        return True
    return False

def get_temp_channel(channel_id):
    data = load_temp_channels()
    return data["channels"].get(str(channel_id))

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"welcome_style": "modern"}
    except Exception as e:
        print(f"❌ Ошибка загрузки настроек: {e}")
        return {"welcome_style": "modern"}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения настроек: {e}")
        return False

def get_welcome_style():
    settings = load_settings()
    style = settings.get("welcome_style", "modern")
    if style not in WELCOME_STYLES:
        style = "modern"
    return style

def set_welcome_style(style_name):
    if style_name not in WELCOME_STYLES:
        return False
    settings = load_settings()
    settings["welcome_style"] = style_name
    return save_settings(settings)

def load_applications_data():
    try:
        if os.path.exists(APPLICATIONS_FILE):
            with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"applications": {}}
    except Exception as e:
        print(f"❌ Ошибка загрузки данных заявок: {e}")
        return {"applications": {}}

def save_applications_data(data):
    try:
        with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения данных заявок: {e}")
        return False

def load_active_chats():
    try:
        if os.path.exists(ACTIVE_CHATS_FILE):
            with open(ACTIVE_CHATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"chats": {}}
    except Exception as e:
        print(f"❌ Ошибка загрузки активных чатов: {e}")
        return {"chats": {}}

def save_active_chats(data):
    try:
        with open(ACTIVE_CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения активных чатов: {e}")
        return False

def load_chat_history():
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"chats": {}}
    except Exception as e:
        print(f"❌ Ошибка загрузки истории чатов: {e}")
        return {"chats": {}}

def save_chat_history(data):
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения истории чатов: {e}")
        return False

def save_application(application_id, user_id, username, content_data, approved_by=None, approved_at=None):
    data = load_applications_data()
    
    data["applications"][str(application_id)] = {
        "user_id": str(user_id),
        "username": username,
        "content": content_data,
        "approved_by": str(approved_by) if approved_by else None,
        "approved_at": approved_at or datetime.now().isoformat(),
        "message_id": None,
        "active_chats": 0,
        "max_chats": 3,
        "is_active": True
    }
    
    save_applications_data(data)
    return True

def update_application_message_id(application_id, message_id):
    data = load_applications_data()
    
    if str(application_id) in data["applications"]:
        data["applications"][str(application_id)]["message_id"] = str(message_id)
        save_applications_data(data)
        return True
    return False

def delete_application(application_id):
    data = load_applications_data()
    if str(application_id) in data["applications"]:
        del data["applications"][str(application_id)]
        save_applications_data(data)
        return True
    return False

def increment_active_chats(application_id):
    data = load_applications_data()
    if str(application_id) in data["applications"]:
        data["applications"][str(application_id)]["active_chats"] += 1
        save_applications_data(data)
        return True
    return False

def decrement_active_chats(application_id):
    data = load_applications_data()
    if str(application_id) in data["applications"]:
        current = data["applications"][str(application_id)]["active_chats"]
        if current > 0:
            data["applications"][str(application_id)]["active_chats"] = current - 1
            save_applications_data(data)
            return True
    return False

def get_active_chats_count(application_id):
    data = load_applications_data()
    if str(application_id) in data["applications"]:
        return data["applications"][str(application_id)].get("active_chats", 0)
    return 0

# ==================== НАСТРОЙКИ СТИЛЕЙ ПРИВЕТСТВИЯ ====================

WELCOME_STYLES = {
    "traditional": {
        "name": "Традиционный китайский",
        "emoji": "🏮",
        "title": "🏮 Добро пожаловать в Небесную Империю!",
        "description": "✨ Приветствую тебя, путник!\nЗдесь, среди облаков и горных вершин,\nтебя ждут новые знакомства и приключения.\n\n⭐ Чтобы ступить на путь культивации,\nнажми на кнопку ниже и пройди регистрацию.\n\n⚠️ **Ты носишь звание {role}**\nПосле церемонии посвящения оно исчезнет.\n\n⚔️ **Мужчина** → станет **Воином**\n🌸 **Женщина** → станет **Цветком**",
        "color": (200, 50, 50),
        "footer": "🌙 Под луной начинается твой путь | Небесные Врата"
    },
    "poetic": {
        "name": "Поэтический",
        "emoji": "🌙",
        "title": "🌙 Добро пожаловать под Луной Небес!",
        "description": "✨ Под светом луны и шелестом бамбука,\nраспахиваются врата этого удивительного мира.\n\n⭐ Пройди путь посвящения,\nи стань частью великой истории.\n\n📜 **Твоя роль:** {role}\nПосле регистрации ты обретёшь новое имя.\n\n⚔️ **Мужской путь** → **Воин**\n🌸 **Женский путь** → **Цветок**",
        "color": (139, 69, 19),
        "footer": "🌸 Там, где цветут сакуры, начинаются легенды"
    },
    "imperial": {
        "name": "Императорский",
        "emoji": "👑",
        "title": "👑 Приветствую в Империи Небесного Дракона!",
        "description": "✨ По указу Небесного Императора,\nврата дворца открываются для достойных.\n\n⭐ Пройди церемонию представления,\nи займи своё место среди избранных.\n\n📜 **Твой титул:** {role}\nПосле посвящения ты обретёшь новый статус.\n\n⚔️ **Мужчина** → **Воин Дракона**\n🌸 **Женщина** → **Цветок Империи**",
        "color": (218, 165, 32),
        "footer": "🏯 Добро пожаловать в Небесный город"
    },
    "modern": {
        "name": "Современный",
        "emoji": "🌸",
        "title": "🌸 Тяньмэнь приветствует тебя!",
        "description": "✨ Добро пожаловать в наше комьюнити,\nгде восточная мудрость встречается с современностью.\n\n⭐ Чтобы стать частью нашей семьи,\nнажми на кнопку и пройди регистрацию.\n\n🎯 **Сейчас ты:** {role}\nПосле регистрации ты получишь доступ ко всему.\n\n⚔️ **Мужчина** → **Воин** (сила и честь)\n🌸 **Женщина** → **Цветок** (грация и красота)",
        "color": (255, 182, 193),
        "footer": "🌙 Под луной начинаются новые знакомства"
    },
    "anime": {
        "name": "Аниме-стиль",
        "emoji": "🎌",
        "title": "🎌 Добро пожаловать в мир аниме!",
        "description": "✨ Привет, искатель приключений!\nТы попал в удивительный мир,\nгде каждый день — это новое приключение.\n\n⭐ Чтобы начать своё путешествие,\nнажми на кнопку и пройди регистрацию.\n\n⚠️ **Твой текущий ранг:** {role}\nПосле повышения ты получишь доступ к новым локациям.\n\n⚔️ **Мужчина** → **Воин** (сила и отвага)\n🌸 **Женщина** → **Цветок** (красота и грация)",
        "color": (255, 105, 180),
        "footer": "🌟 Пусть удача сопутствует тебе в этом мире!"
    },
    "minimal": {
        "name": "Минималистичный",
        "emoji": "✦",
        "title": "✦ Добро пожаловать",
        "description": "Приветствуем нового участника.\nДля получения доступа к серверу,\nпройдите регистрацию.\n\nРоль: {role}\nПосле регистрации будет заменена.\n\nМужчина → Воин\nЖенщина → Цветок",
        "color": (100, 100, 100),
        "footer": "Добро пожаловать в сообщество"
    }
}

# ==================== КЛАССЫ ДЛЯ ЧАТОВ ====================

class ChatManager:
    @staticmethod
    def start_chat(application_id, from_user_id, to_user_id, is_anonymous=False):
        data = load_active_chats()
        chat_id = f"chat_{application_id}_{from_user_id}_{int(datetime.now().timestamp())}"
        
        # Проверяем, есть ли уже активный чат между этими пользователями
        for existing_chat_id, chat in data["chats"].items():
            if (chat.get("application_id") == str(application_id) and chat.get("is_active", False) and
                ((chat.get("from_user_id") == str(from_user_id) and chat.get("to_user_id") == str(to_user_id)) or
                 (chat.get("from_user_id") == str(to_user_id) and chat.get("to_user_id") == str(from_user_id)))):
                return existing_chat_id
        
        data["chats"][chat_id] = {
            "application_id": str(application_id),
            "from_user_id": str(from_user_id),
            "to_user_id": str(to_user_id),
            "started_at": datetime.now().isoformat(),
            "is_active": True,
            "messages": [],
            "channel_id": None,
            "is_anonymous": is_anonymous
        }
        
        save_active_chats(data)
        increment_active_chats(application_id)
        return chat_id
    
    @staticmethod
    def end_chat(chat_id):
        data = load_active_chats()
        if chat_id in data["chats"]:
            chat = data["chats"][chat_id]
            if chat.get("is_active", False):
                chat["is_active"] = False
                chat["ended_at"] = datetime.now().isoformat()
                save_active_chats(data)
                decrement_active_chats(chat.get("application_id", ""))
                return True
        return False
    
    @staticmethod
    def get_active_chat_for_application(application_id):
        data = load_active_chats()
        active_chats = []
        for chat_id, chat in data["chats"].items():
            if chat.get("application_id") == str(application_id) and chat.get("is_active", False):
                active_chats.append((chat_id, chat))
        return active_chats
    
    @staticmethod
    def get_active_chats_for_user(user_id):
        data = load_active_chats()
        user_chats = []
        for chat_id, chat in data["chats"].items():
            if chat.get("is_active", False) and (str(chat.get("from_user_id", "")) == str(user_id) or str(chat.get("to_user_id", "")) == str(user_id)):
                user_chats.append((chat_id, chat))
        return user_chats
    
    @staticmethod
    def is_user_in_chat(user_id, chat_id):
        data = load_active_chats()
        if chat_id in data["chats"]:
            chat = data["chats"][chat_id]
            return str(chat.get("from_user_id", "")) == str(user_id) or str(chat.get("to_user_id", "")) == str(user_id)
        return False
    
    @staticmethod
    def add_message(chat_id, from_user_id, message):
        data = load_active_chats()
        if chat_id in data["chats"] and data["chats"][chat_id].get("is_active", False):
            data["chats"][chat_id]["messages"].append({
                "from": str(from_user_id),
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            save_active_chats(data)
            return True
        return False
    
    @staticmethod
    def get_other_user(chat_id, user_id):
        data = load_active_chats()
        if chat_id in data["chats"]:
            chat = data["chats"][chat_id]
            if str(chat.get("from_user_id", "")) == str(user_id):
                return chat.get("to_user_id")
            elif str(chat.get("to_user_id", "")) == str(user_id):
                return chat.get("from_user_id")
        return None
    
    @staticmethod
    def get_chat_messages(chat_id, limit=50):
        data = load_active_chats()
        if chat_id in data["chats"]:
            messages = data["chats"][chat_id].get("messages", [])
            return messages[-limit:]
        return []
    
    @staticmethod
    def get_chat_by_id(chat_id):
        data = load_active_chats()
        return data["chats"].get(chat_id)

# ==================== МОДАЛЬНОЕ ОКНО ДЛЯ АНОНИМНОСТИ ====================

class AnonymousModal(Modal):
    def __init__(self, application_id, author_id, requester_id):
        super().__init__(title="🔒 Настройки чата")
        self.application_id = application_id
        self.author_id = author_id
        self.requester_id = requester_id
        
        self.anonymous_choice = TextInput(
            label="Анонимный чат? (да/нет)",
            placeholder="Введите 'да' или 'нет'",
            default="да",
            required=True,
            max_length=10
        )
        self.add_item(self.anonymous_choice)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            choice = self.anonymous_choice.value.lower().strip()
            is_anonymous = choice in ["да", "yes", "true", "1"]
            
            if choice not in ["да", "нет", "yes", "no", "true", "false", "1", "0"]:
                await interaction.response.send_message("❌ Введите 'да' или 'нет'!", ephemeral=True)
                return
            
            # Создаем чат
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("❌ Эта функция доступна только на сервере!", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            
            chat_id = ChatManager.start_chat(self.application_id, self.author_id, self.requester_id, is_anonymous)
            
            channel = await TemporaryChannelManager.create_channel(
                guild,
                self.author_id,
                self.requester_id,
                self.application_id,
                is_anonymous
            )
            
            if channel:
                try:
                    owner = await bot.fetch_user(int(self.author_id))
                    if owner:
                        embed = discord.Embed(
                            title="💌 Создан приватный чат!",
                            description=f"{interaction.user.mention} начал(а) с вами чат!\n\n"
                                       f"📌 Перейдите в канал: {channel.mention}\n"
                                       f"🔒 Режим: {'Анонимный' if is_anonymous else 'Открытый'}",
                            color=discord.Color.green()
                        )
                        await owner.send(embed=embed)
                except Exception as e:
                    print(f"Ошибка уведомления автора: {e}")
                
                await interaction.followup.send(
                    f"✅ Чат создан! Перейдите в канал: {channel.mention}\n"
                    f"🔒 Режим: {'Анонимный' if is_anonymous else 'Открытый'}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("❌ Не удалось создать чат. Попробуйте позже.", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка в AnonymousModal: {e}")
            await interaction.response.send_message("❌ Произошла ошибка. Попробуйте позже.", ephemeral=True)

# ==================== УПРАВЛЕНИЕ ВРЕМЕННЫМИ КАНАЛАМИ ====================

class TemporaryChannelManager:
    @staticmethod
    async def create_channel(guild, user1_id, user2_id, application_id, is_anonymous=False):
        try:
            user1 = await bot.fetch_user(int(user1_id))
            user2 = await bot.fetch_user(int(user2_id))
            
            if not user1 or not user2:
                print(f"❌ Не удалось получить пользователей: {user1_id}, {user2_id}")
                return None
            
            # Для анонимного чата используем общие имена
            if is_anonymous:
                name1 = "Аноним"
                name2 = "Аноним"
                channel_name = f"💬-Аноним-{random.randint(1000, 9999)}"
            else:
                name1 = re.sub(r'[^a-zA-Z0-9а-яА-Я]', '', user1.name)[:8]
                name2 = re.sub(r'[^a-zA-Z0-9а-яА-Я]', '', user2.name)[:8]
                channel_name = f"💬-{name1}-{name2}"
            
            # Права доступа
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_messages=True,
                    read_messages=True
                ),
                user1: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                    add_reactions=True,
                    read_messages=True
                ),
                user2: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                    add_reactions=True,
                    read_messages=True
                )
            }
            
            # Добавляем админов с правом только чтения
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        read_messages=True,
                        read_message_history=True,
                        send_messages=False
                    )
            
            category_name = "💬 Приватные чаты"
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                try:
                    category = await guild.create_category(category_name)
                    print(f"✅ Создана категория: {category_name}")
                except Exception as e:
                    print(f"❌ Ошибка создания категории: {e}")
                    return None
            
            try:
                channel = await guild.create_text_channel(
                    channel_name,
                    category=category,
                    overwrites=overwrites,
                    topic=f"Приватный чат | ID: {application_id[:8]} | {'Анонимный' if is_anonymous else 'Открытый'}"
                )
                print(f"✅ Создан приватный канал: {channel.name}")
            except Exception as e:
                print(f"❌ Ошибка создания канала: {e}")
                return None
            
            add_temp_channel(channel.id, application_id, user1_id, user2_id, is_anonymous)
            
            # Обновляем информацию в чате
            active_chats = ChatManager.get_active_chat_for_application(application_id)
            for chat_id, chat in active_chats:
                if (str(chat.get("from_user_id")) == str(user1_id) and str(chat.get("to_user_id")) == str(user2_id)) or \
                   (str(chat.get("from_user_id")) == str(user2_id) and str(chat.get("to_user_id")) == str(user1_id)):
                    data = load_active_chats()
                    if chat_id in data["chats"]:
                        data["chats"][chat_id]["channel_id"] = str(channel.id)
                        data["chats"][chat_id]["is_anonymous"] = is_anonymous
                        save_active_chats(data)
                    break
            
            # Получаем количество активных чатов у владельца анкеты
            owner_chats_count = get_active_chats_count(application_id)
            
            embed = discord.Embed(
                title="💬 Добро пожаловать в приватный чат!",
                description=f"Вы общаетесь с другим участником сервера.\n\n"
                           f"📌 **Правила:**\n"
                           f"• Будьте вежливы друг с другом\n"
                           f"• Не используйте оскорбления\n"
                           f"• Наслаждайтесь общением!\n\n"
                           f"🔒 **Режим:** {'Анонимный' if is_anonymous else 'Открытый'}\n"
                           f"📊 **Статус:** У вас активно {owner_chats_count} чатов из 3 возможных.",
                color=discord.Color.green()
            )
            
            if is_anonymous:
                embed.add_field(
                    name="🕵️ Анонимный режим",
                    value="Ваши имена скрыты! Вы общаетесь как 'Аноним'.",
                    inline=False
                )
            
            embed.set_footer(text="🔒 Ваш чат приватный и защищенный")
            
            view = ChatChannelView(channel.id, user1_id, user2_id, application_id, is_anonymous)
            
            try:
                await channel.send(embed=embed, view=view)
                await channel.send(f"{user1.mention} {user2.mention}, приятного общения! 🎉")
            except Exception as e:
                print(f"❌ Ошибка отправки приветствия: {e}")
            
            return channel
            
        except Exception as e:
            print(f"❌ Ошибка создания канала: {e}")
            traceback.print_exc()
            return None
    
    @staticmethod
    async def delete_channel(channel):
        try:
            if channel:
                remove_temp_channel(channel.id)
                await channel.delete(reason="Временный чат завершен")
                print(f"✅ Удален канал: {channel.name}")
                return True
        except Exception as e:
            print(f"❌ Ошибка удаления канала: {e}")
            return False
    
    @staticmethod
    async def archive_chat(chat_id, channel):
        """Сохраняет историю чата в архив"""
        try:
            chat_data = ChatManager.get_chat_by_id(chat_id)
            if not chat_data:
                return
            
            messages = chat_data.get("messages", [])
            if not messages:
                return
            
            # Получаем информацию о пользователях
            user1_id = chat_data.get("from_user_id")
            user2_id = chat_data.get("to_user_id")
            is_anonymous = chat_data.get("is_anonymous", False)
            
            try:
                user1 = await bot.fetch_user(int(user1_id))
                user2 = await bot.fetch_user(int(user2_id))
                user1_name = user1.name if user1 else "Неизвестно"
                user2_name = user2.name if user2 else "Неизвестно"
            except:
                user1_name = "Неизвестно"
                user2_name = "Неизвестно"
            
            # Формируем историю
            history_text = []
            for msg in messages:
                try:
                    sender = await bot.fetch_user(int(msg["from"]))
                    sender_name = sender.name if sender else "Неизвестно"
                except:
                    sender_name = "Неизвестно"
                
                # В анонимном режиме скрываем имена
                if is_anonymous:
                    if msg["from"] == user1_id:
                        sender_name = "Аноним #1"
                    elif msg["from"] == user2_id:
                        sender_name = "Аноним #2"
                
                timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%d.%m.%Y %H:%M:%S")
                history_text.append(f"[{timestamp}] {sender_name}: {msg['message']}")
            
            full_history = "\n".join(history_text)
            
            # Сохраняем в файл
            history_data = load_chat_history()
            history_data["chats"][chat_id] = {
                "user1_id": user1_id,
                "user1_name": user1_name,
                "user2_id": user2_id,
                "user2_name": user2_name,
                "is_anonymous": is_anonymous,
                "started_at": chat_data.get("started_at"),
                "ended_at": chat_data.get("ended_at", datetime.now().isoformat()),
                "messages": messages,
                "full_history": full_history
            }
            save_chat_history(history_data)
            
            # Отправляем в архивный канал
            archive_channel = discord.utils.get(channel.guild.channels, name=ARCHIVE_CHANNEL_NAME)
            if not archive_channel:
                # Создаем архивный канал
                overwrites = {
                    channel.guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                    channel.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
                }
                try:
                    archive_channel = await channel.guild.create_text_channel(
                        ARCHIVE_CHANNEL_NAME,
                        overwrites=overwrites,
                        topic="Архив завершенных чатов"
                    )
                    print(f"✅ Создан архивный канал: {archive_channel.name}")
                except Exception as e:
                    print(f"❌ Ошибка создания архивного канала: {e}")
                    return
            
            if archive_channel:
                embed = discord.Embed(
                    title=f"📜 Архив чата",
                    description=f"**Чат между:** {user1_name} и {user2_name}\n"
                               f"**Режим:** {'Анонимный' if is_anonymous else 'Открытый'}\n"
                               f"**Сообщений:** {len(messages)}\n"
                               f"**Начат:** {chat_data.get('started_at', '')[:16]}\n"
                               f"**Завершен:** {chat_data.get('ended_at', datetime.now().isoformat())[:16]}",
                    color=discord.Color.blue()
                )
                
                # Показываем первые 10 сообщений, остальное скрыто
                preview = "\n".join(history_text[:10])
                if len(history_text) > 10:
                    preview += f"\n... и еще {len(history_text) - 10} сообщений"
                
                embed.add_field(name="📝 Превью (первые 10 сообщений)", value=f"```\n{preview[:1000]}\n```", inline=False)
                embed.add_field(name="📊 Полная история", value="Нажмите кнопку ниже, чтобы увидеть полную историю", inline=False)
                
                view = ArchiveView(chat_id)
                await archive_channel.send(embed=embed, view=view)
                
        except Exception as e:
            print(f"❌ Ошибка архивации чата: {e}")

# ==================== КНОПКИ ДЛЯ АРХИВА ====================

class ArchiveView(View):
    def __init__(self, chat_id):
        super().__init__(timeout=3600)
        self.chat_id = chat_id
    
    @discord.ui.button(label='📜 Показать полную историю', style=discord.ButtonStyle.primary, custom_id='show_full_archive')
    async def show_full_archive(self, interaction: discord.Interaction, button: Button):
        try:
            history_data = load_chat_history()
            chat_data = history_data["chats"].get(self.chat_id)
            
            if not chat_data:
                await interaction.response.send_message("❌ История не найдена!", ephemeral=True)
                return
            
            full_history = chat_data.get("full_history", "")
            if not full_history:
                await interaction.response.send_message("❌ История пуста!", ephemeral=True)
                return
            
            # Разбиваем на части
            if len(full_history) > 1900:
                parts = [full_history[i:i+1900] for i in range(0, len(full_history), 1900)]
                for i, part in enumerate(parts):
                    embed = discord.Embed(
                        title=f"📜 Полная история чата (часть {i+1}/{len(parts)})",
                        description=f"```\n{part}\n```",
                        color=discord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    if i < len(parts) - 1:
                        await asyncio.sleep(0.5)
            else:
                embed = discord.Embed(
                    title="📜 Полная история чата",
                    description=f"```\n{full_history}\n```",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка показа архива: {e}")
            await interaction.response.send_message("❌ Ошибка при показе истории!", ephemeral=True)

# ==================== КНОПКИ ДЛЯ ЗАПРОСА РАЗРЕШЕНИЯ ====================

class PermissionRequestView(View):
    def __init__(self, application_id, requester_id, owner_id):
        super().__init__(timeout=300)
        self.application_id = application_id
        self.requester_id = requester_id
        self.owner_id = owner_id
        self.response = None
    
    @discord.ui.button(label='✅ Разрешить', style=discord.ButtonStyle.success, custom_id='permit_chat')
    async def permit_chat(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(self.owner_id):
            await interaction.response.send_message("❌ Это сообщение не для вас!", ephemeral=True)
            return
        
        self.response = "permit"
        self.stop()
        
        await interaction.response.send_message("✅ Вы разрешили начать чат!", ephemeral=True)
        
        try:
            requester = await bot.fetch_user(int(self.requester_id))
            if requester:
                embed = discord.Embed(
                    title="✅ Разрешение получено!",
                    description="Владелец анкеты разрешил начать чат.\n\n"
                               "📌 Теперь выберите режим чата:",
                    color=discord.Color.green()
                )
                modal = AnonymousModal(self.application_id, self.owner_id, self.requester_id)
                await requester.send(embed=embed)
                await requester.send("Нажмите кнопку ниже, чтобы настроить чат:", view=AnonymousStartView(self.application_id, self.owner_id, self.requester_id))
        except Exception as e:
            print(f"❌ Ошибка уведомления: {e}")
    
    @discord.ui.button(label='❌ Отказать', style=discord.ButtonStyle.danger, custom_id='deny_chat')
    async def deny_chat(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(self.owner_id):
            await interaction.response.send_message("❌ Это сообщение не для вас!", ephemeral=True)
            return
        
        self.response = "deny"
        self.stop()
        
        await interaction.response.send_message("❌ Вы отказали в начале чата.", ephemeral=True)
        
        try:
            requester = await bot.fetch_user(int(self.requester_id))
            if requester:
                await requester.send("❌ Владелец анкеты отказал в начале чата. Попробуйте позже.")
        except:
            pass
    
    @discord.ui.button(label='🚫 Заблокировать', style=discord.ButtonStyle.danger, custom_id='block_user_from_request')
    async def block_user_from_request(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(self.owner_id):
            await interaction.response.send_message("❌ Это сообщение не для вас!", ephemeral=True)
            return
        
        if block_user(self.owner_id, self.requester_id):
            self.response = "block"
            self.stop()
            
            await interaction.response.send_message("🚫 Пользователь заблокирован!", ephemeral=True)
            
            try:
                requester = await bot.fetch_user(int(self.requester_id))
                if requester:
                    await requester.send("🚫 Владелец анкеты заблокировал вас!")
            except:
                pass
        else:
            await interaction.response.send_message("❌ Ошибка при блокировке!", ephemeral=True)

class AnonymousStartView(View):
    def __init__(self, application_id, author_id, requester_id):
        super().__init__(timeout=300)
        self.application_id = application_id
        self.author_id = author_id
        self.requester_id = requester_id
    
    @discord.ui.button(label='🔒 Анонимный чат', style=discord.ButtonStyle.secondary, custom_id='anonymous_chat')
    async def anonymous_chat(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(self.requester_id):
            await interaction.response.send_message("❌ Это сообщение не для вас!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ Эта функция доступна только на сервере!", ephemeral=True)
            return
        
        chat_id = ChatManager.start_chat(self.application_id, self.author_id, self.requester_id, True)
        
        channel = await TemporaryChannelManager.create_channel(
            guild,
            self.author_id,
            self.requester_id,
            self.application_id,
            True
        )
        
        if channel:
            try:
                owner = await bot.fetch_user(int(self.author_id))
                if owner:
                    embed = discord.Embed(
                        title="💌 Создан приватный чат!",
                        description=f"{interaction.user.mention} начал(а) с вами чат!\n\n"
                                   f"📌 Перейдите в канал: {channel.mention}\n"
                                   f"🔒 Режим: Анонимный",
                        color=discord.Color.green()
                    )
                    await owner.send(embed=embed)
            except Exception as e:
                print(f"Ошибка уведомления автора: {e}")
            
            await interaction.followup.send(f"✅ Анонимный чат создан! Перейдите в канал: {channel.mention}", ephemeral=True)
        else:
            await interaction.followup.send("❌ Не удалось создать чат. Попробуйте позже.", ephemeral=True)
    
    @discord.ui.button(label='👤 Открытый чат', style=discord.ButtonStyle.primary, custom_id='open_chat')
    async def open_chat(self, interaction: discord.Interaction, button: Button):
        if str(interaction.user.id) != str(self.requester_id):
            await interaction.response.send_message("❌ Это сообщение не для вас!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("❌ Эта функция доступна только на сервере!", ephemeral=True)
            return
        
        chat_id = ChatManager.start_chat(self.application_id, self.author_id, self.requester_id, False)
        
        channel = await TemporaryChannelManager.create_channel(
            guild,
            self.author_id,
            self.requester_id,
            self.application_id,
            False
        )
        
        if channel:
            try:
                owner = await bot.fetch_user(int(self.author_id))
                if owner:
                    embed = discord.Embed(
                        title="💌 Создан приватный чат!",
                        description=f"{interaction.user.mention} начал(а) с вами чат!\n\n"
                                   f"📌 Перейдите в канал: {channel.mention}\n"
                                   f"🔒 Режим: Открытый",
                        color=discord.Color.green()
                    )
                    await owner.send(embed=embed)
            except Exception as e:
                print(f"Ошибка уведомления автора: {e}")
            
            await interaction.followup.send(f"✅ Открытый чат создан! Перейдите в канал: {channel.mention}", ephemeral=True)
        else:
            await interaction.followup.send("❌ Не удалось создать чат. Попробуйте позже.", ephemeral=True)

# ==================== КНОПКИ ДЛЯ ИСТОРИИ ====================

class HistoryView(View):
    def __init__(self, chat_id, messages):
        super().__init__(timeout=300)
        self.chat_id = chat_id
        self.messages = messages
        self.show_full = False
    
    @discord.ui.button(label='📜 Показать полностью', style=discord.ButtonStyle.primary, custom_id='show_full_history')
    async def show_full_history(self, interaction: discord.Interaction, button: Button):
        if not ChatManager.is_user_in_chat(interaction.user.id, self.chat_id):
            await interaction.response.send_message("❌ Вы не являетесь участником этого чата!", ephemeral=True)
            return
        
        self.show_full = True
        
        # Получаем информацию об анонимности
        chat_data = ChatManager.get_chat_by_id(self.chat_id)
        is_anonymous = chat_data.get("is_anonymous", False) if chat_data else False
        user1_id = chat_data.get("from_user_id") if chat_data else None
        user2_id = chat_data.get("to_user_id") if chat_data else None
        
        history_text = []
        for msg in self.messages:
            try:
                sender = await bot.fetch_user(int(msg["from"]))
                sender_name = sender.name if sender else "Неизвестно"
            except:
                sender_name = "Неизвестно"
            
            if is_anonymous:
                if msg["from"] == user1_id:
                    sender_name = "Аноним #1"
                elif msg["from"] == user2_id:
                    sender_name = "Аноним #2"
            
            timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%d.%m.%Y %H:%M")
            history_text.append(f"**[{timestamp}] {sender_name}:** {msg['message']}")
        
        full_history = "\n".join(history_text)
        
        if len(full_history) > 1900:
            parts = [full_history[i:i+1900] for i in range(0, len(full_history), 1900)]
            for i, part in enumerate(parts):
                embed = discord.Embed(
                    title=f"📜 Полная история чата (часть {i+1}/{len(parts)})",
                    description=f"```\n{part}\n```",
                    color=discord.Color.blue()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                if i < len(parts) - 1:
                    await asyncio.sleep(0.5)
        else:
            embed = discord.Embed(
                title="📜 Полная история чата",
                description=f"```\n{full_history}\n```",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        button.label = '📜 Скрыть'
        button.style = discord.ButtonStyle.secondary
        await interaction.message.edit(view=self)
    
    @discord.ui.button(label='🔒 Закрыть', style=discord.ButtonStyle.danger, custom_id='close_history')
    async def close_history(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("✅ История закрыта.", ephemeral=True)
        self.stop()

# ==================== КНОПКИ ДЛЯ КАНАЛА ====================

class ChatChannelView(View):
    def __init__(self, channel_id, user1_id, user2_id, application_id, is_anonymous=False):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.application_id = application_id
        self.is_anonymous = is_anonymous
        self.last_activity = datetime.now()
    
    @discord.ui.button(label='🔒 Завершить чат', style=discord.ButtonStyle.danger, custom_id='close_chat_channel')
    async def close_chat(self, interaction: discord.Interaction, button: Button):
        try:
            if str(interaction.user.id) not in [str(self.user1_id), str(self.user2_id)]:
                await interaction.response.send_message("❌ Вы не являетесь участником этого чата!", ephemeral=True)
                return
            
            channel = interaction.channel
            
            if channel.id != self.channel_id:
                await interaction.response.send_message("❌ Это не тот канал!", ephemeral=True)
                return
            
            other_user_id = self.user2_id if str(interaction.user.id) == str(self.user1_id) else self.user1_id
            
            # Получаем ID чата
            chat_id = None
            active_chats = ChatManager.get_active_chat_for_application(self.application_id)
            for cid, chat in active_chats:
                if (str(chat.get("from_user_id")) == str(self.user1_id) and str(chat.get("to_user_id")) == str(self.user2_id)) or \
                   (str(chat.get("from_user_id")) == str(self.user2_id) and str(chat.get("to_user_id")) == str(self.user1_id)):
                    chat_id = cid
                    break
            
            try:
                other_user = await bot.fetch_user(int(other_user_id))
                if other_user:
                    try:
                        await other_user.send(f"🔒 {interaction.user.mention} завершил(а) чат с вами. Канал будет удален.")
                    except:
                        pass
            except:
                pass
            
            embed = discord.Embed(
                title="🔒 Чат завершен",
                description=f"{interaction.user.mention} завершил(а) чат.\nКанал будет удален через 5 секунд.",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
            
            await interaction.response.send_message("✅ Чат завершен! Канал будет удален...", ephemeral=True)
            
            # Архивируем чат
            if chat_id:
                await TemporaryChannelManager.archive_chat(chat_id, channel)
                ChatManager.end_chat(chat_id)
            
            await asyncio.sleep(5)
            await TemporaryChannelManager.delete_channel(channel)
            
        except Exception as e:
            print(f"❌ Ошибка при завершении чата: {e}")
            try:
                await interaction.response.send_message("❌ Ошибка при завершении чата!", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label='🚫 Заблокировать', style=discord.ButtonStyle.danger, custom_id='block_chat_channel')
    async def block_user_in_chat(self, interaction: discord.Interaction, button: Button):
        try:
            if str(interaction.user.id) not in [str(self.user1_id), str(self.user2_id)]:
                await interaction.response.send_message("❌ Вы не являетесь участником этого чата!", ephemeral=True)
                return
            
            channel = interaction.channel
            
            if channel.id != self.channel_id:
                await interaction.response.send_message("❌ Это не тот канал!", ephemeral=True)
                return
            
            other_user_id = self.user2_id if str(interaction.user.id) == str(self.user1_id) else self.user1_id
            
            if str(interaction.user.id) == str(other_user_id):
                await interaction.response.send_message("❌ Вы не можете заблокировать себя!", ephemeral=True)
                return
            
            if block_user(interaction.user.id, other_user_id):
                chat_id = None
                active_chats = ChatManager.get_active_chat_for_application(self.application_id)
                for cid, chat in active_chats:
                    if (str(chat.get("from_user_id")) == str(self.user1_id) and str(chat.get("to_user_id")) == str(self.user2_id)) or \
                       (str(chat.get("from_user_id")) == str(self.user2_id) and str(chat.get("to_user_id")) == str(self.user1_id)):
                        chat_id = cid
                        break
                
                try:
                    other_user = await bot.fetch_user(int(other_user_id))
                    if other_user:
                        try:
                            await other_user.send(f"🚫 {interaction.user.mention} заблокировал(а) вас. Чат завершен.")
                        except:
                            pass
                except:
                    pass
                
                embed = discord.Embed(
                    title="🚫 Пользователь заблокирован",
                    description=f"{interaction.user.mention} заблокировал(а) другого участника.\nКанал будет удален через 5 секунд.",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                
                await interaction.response.send_message("✅ Пользователь заблокирован! Канал будет удален...", ephemeral=True)
                
                if chat_id:
                    await TemporaryChannelManager.archive_chat(chat_id, channel)
                    ChatManager.end_chat(chat_id)
                
                await asyncio.sleep(5)
                await TemporaryChannelManager.delete_channel(channel)
                
            else:
                await interaction.response.send_message("❌ Ошибка при блокировке пользователя!", ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка при блокировке: {e}")
            try:
                await interaction.response.send_message("❌ Ошибка при блокировке!", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label='📜 История', style=discord.ButtonStyle.secondary, custom_id='show_history')
    async def show_history(self, interaction: discord.Interaction, button: Button):
        try:
            if str(interaction.user.id) not in [str(self.user1_id), str(self.user2_id)]:
                await interaction.response.send_message("❌ Вы не являетесь участником этого чата!", ephemeral=True)
                return
            
            channel = interaction.channel
            
            if channel.id != self.channel_id:
                await interaction.response.send_message("❌ Это не тот канал!", ephemeral=True)
                return
            
            chat_id = None
            active_chats = ChatManager.get_active_chat_for_application(self.application_id)
            for cid, chat in active_chats:
                if (str(chat.get("from_user_id")) == str(self.user1_id) and str(chat.get("to_user_id")) == str(self.user2_id)) or \
                   (str(chat.get("from_user_id")) == str(self.user2_id) and str(chat.get("to_user_id")) == str(self.user1_id)):
                    chat_id = cid
                    break
            
            if not chat_id:
                await interaction.response.send_message("❌ Чат не найден!", ephemeral=True)
                return
            
            messages = ChatManager.get_chat_messages(chat_id, limit=50)
            
            if not messages:
                await interaction.response.send_message("📭 История пуста.", ephemeral=True)
                return
            
            chat_data = ChatManager.get_chat_by_id(chat_id)
            is_anonymous = chat_data.get("is_anonymous", False) if chat_data else False
            user1_id = chat_data.get("from_user_id") if chat_data else None
            user2_id = chat_data.get("to_user_id") if chat_data else None
            
            preview_text = []
            for msg in messages[:5]:
                try:
                    sender = await bot.fetch_user(int(msg["from"]))
                    sender_name = sender.name if sender else "Неизвестно"
                except:
                    sender_name = "Неизвестно"
                
                if is_anonymous:
                    if msg["from"] == user1_id:
                        sender_name = "Аноним #1"
                    elif msg["from"] == user2_id:
                        sender_name = "Аноним #2"
                
                timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%d.%m.%Y %H:%M")
                msg_text = msg["message"]
                if len(msg_text) > 20:
                    msg_text = msg_text[:20] + "..."
                preview_text.append(f"**[{timestamp}] {sender_name}:** {msg_text}")
            
            preview = "\n".join(preview_text)
            total_messages = len(messages)
            
            embed = discord.Embed(
                title="📜 История сообщений",
                description=f"**Всего сообщений:** {total_messages}\n"
                           f"**Режим:** {'Анонимный' if is_anonymous else 'Открытый'}\n\n"
                           f"**Последние 5 сообщений:**\n```\n{preview}\n```",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Нажмите 'Показать полностью' для всей истории")
            
            view = HistoryView(chat_id, messages)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Ошибка при показе истории: {e}")
            try:
                await interaction.response.send_message("❌ Ошибка при показе истории!", ephemeral=True)
            except:
                pass
    
    @discord.ui.button(label='⭐ Оценить', style=discord.ButtonStyle.success, custom_id='rate_chat')
    async def rate_chat(self, interaction: discord.Interaction, button: Button):
        try:
            if str(interaction.user.id) not in [str(self.user1_id), str(self.user2_id)]:
                await interaction.response.send_message("❌ Вы не являетесь участником этого чата!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="⭐ Оцените собеседника",
                description="Как прошло общение?",
                color=discord.Color.gold()
            )
            
            view = RatingView(self.application_id, self.user1_id, self.user2_id, interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Ошибка при оценке: {e}")
            await interaction.response.send_message("❌ Ошибка при оценке!", ephemeral=True)

# ==================== КНОПКИ ДЛЯ ОЦЕНКИ ====================

class RatingView(View):
    def __init__(self, application_id, user1_id, user2_id, rater_id):
        super().__init__(timeout=60)
        self.application_id = application_id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.rater_id = rater_id
        self.rated = False
    
    @discord.ui.button(label='⭐ 1', style=discord.ButtonStyle.secondary, custom_id='rate_1')
    async def rate_1(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 1)
    
    @discord.ui.button(label='⭐ 2', style=discord.ButtonStyle.secondary, custom_id='rate_2')
    async def rate_2(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 2)
    
    @discord.ui.button(label='⭐ 3', style=discord.ButtonStyle.secondary, custom_id='rate_3')
    async def rate_3(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 3)
    
    @discord.ui.button(label='⭐ 4', style=discord.ButtonStyle.secondary, custom_id='rate_4')
    async def rate_4(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 4)
    
    @discord.ui.button(label='⭐ 5', style=discord.ButtonStyle.secondary, custom_id='rate_5')
    async def rate_5(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 5)
    
    async def handle_rating(self, interaction: discord.Interaction, rating: int):
        if self.rated:
            await interaction.response.send_message("❌ Вы уже оценили!", ephemeral=True)
            return
        
        if str(interaction.user.id) != str(self.rater_id):
            await interaction.response.send_message("❌ Это не ваша оценка!", ephemeral=True)
            return
        
        self.rated = True
        other_user_id = self.user2_id if str(interaction.user.id) == str(self.user1_id) else self.user1_id
        
        try:
            other_user = await bot.fetch_user(int(other_user_id))
            if other_user:
                embed = discord.Embed(
                    title="⭐ Новая оценка!",
                    description=f"{interaction.user.mention} оценил(а) вас на {rating} ⭐",
                    color=discord.Color.gold()
                )
                await other_user.send(embed=embed)
        except:
            pass
        
        await interaction.response.send_message(f"✅ Оценка {rating} ⭐ сохранена!", ephemeral=True)
        self.stop()

# ==================== КНОПКИ ДЛЯ ЗАЯВКИ ====================

class ChatButtons(View):
    def __init__(self, application_id, author_id, message_id=None):
        super().__init__(timeout=None)
        self.application_id = application_id
        self.author_id = author_id
        self.message_id = message_id
    
    @discord.ui.button(label='💬 Начать чат', style=discord.ButtonStyle.success, custom_id='start_chat_from_app')
    async def start_chat(self, interaction: discord.Interaction, button: Button):
        try:
            if str(interaction.user.id) == str(self.author_id):
                await interaction.response.send_message("❌ Вы не можете начать чат с самим собой!", ephemeral=True)
                return
            
            data = load_applications_data()
            app_data = data["applications"].get(str(self.application_id))
            if not app_data:
                await interaction.response.send_message("❌ Эта заявка уже удалена!", ephemeral=True)
                return
            
            if is_user_blocked(self.author_id, interaction.user.id):
                await interaction.response.send_message("❌ Автор заявки заблокировал вас!", ephemeral=True)
                return
            
            if is_user_blocked(interaction.user.id, self.author_id):
                await interaction.response.send_message("❌ Вы заблокировали автора заявки!", ephemeral=True)
                return
            
            # Проверяем, есть ли уже активный чат между этими пользователями
            active_chats = ChatManager.get_active_chat_for_application(self.application_id)
            for chat_id, chat in active_chats:
                if (str(chat.get("from_user_id")) == str(self.author_id) and str(chat.get("to_user_id")) == str(interaction.user.id)) or \
                   (str(chat.get("from_user_id")) == str(interaction.user.id) and str(chat.get("to_user_id")) == str(self.author_id)):
                    channel_id = chat.get("channel_id")
                    if channel_id:
                        channel = bot.get_channel(int(channel_id))
                        if channel:
                            await interaction.response.send_message(f"✅ Вы уже общаетесь в чате! Перейдите в канал: {channel.mention}", ephemeral=True)
                            return
                        else:
                            pass
            
            # Проверяем количество активных чатов у владельца
            active_chats_count = get_active_chats_count(self.application_id)
            max_chats = app_data.get("max_chats", 3)
            
            # Если уже есть 1 активный чат, запрашиваем разрешение на второй
            if active_chats_count >= 1:
                try:
                    owner = await bot.fetch_user(int(self.author_id))
                    if owner:
                        embed = discord.Embed(
                            title="❓ Запрос на начало чата",
                            description=f"Пользователь {interaction.user.mention} хочет начать с вами чат.\n\n"
                                       f"📊 **У вас уже активно {active_chats_count} чатов из {max_chats}.**\n"
                                       f"Разрешить начать еще один чат?",
                            color=discord.Color.gold()
                        )
                        embed.add_field(
                            name="ℹ️ Информация о пользователе",
                            value=f"ID: {interaction.user.id}\nИмя: {interaction.user.name}",
                            inline=False
                        )
                        
                        view = PermissionRequestView(self.application_id, interaction.user.id, self.author_id)
                        
                        await owner.send(embed=embed, view=view)
                        await interaction.response.send_message(
                            "📨 Владельцу анкеты отправлен запрос на разрешение чата. Ожидайте ответа.",
                            ephemeral=True
                        )
                        return
                except Exception as e:
                    print(f"❌ Ошибка отправки запроса владельцу: {e}")
                    await interaction.response.send_message("❌ Не удалось отправить запрос владельцу анкеты.", ephemeral=True)
                    return
            
            # Если чатов нет, сразу предлагаем выбор анонимности
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("❌ Эта функция доступна только на сервере!", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            
            # Отправляем выбор режима
            embed = discord.Embed(
                title="🔒 Выберите режим чата",
                description="Как вы хотите общаться?",
                color=discord.Color.blue()
            )
            
            view = AnonymousStartView(self.application_id, self.author_id, interaction.user.id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                
        except Exception as e:
            print(f"❌ Ошибка в start_chat: {e}")
            try:
                await interaction.response.send_message("❌ Произошла ошибка. Попробуйте позже.", ephemeral=True)
            except:
                pass

# ==================== МОДАЛЬНОЕ ОКНО ДЛЯ РЕДАКТИРОВАНИЯ ====================

class EditApplicationModal(Modal):
    def __init__(self, application_data, original_message, view, user_id):
        super().__init__(title="✏️ Редактирование заявки")
        self.application_data = application_data
        self.original_message = original_message
        self.parent_view = view
        self.user_id = user_id
        
        self.name_input = TextInput(
            label="🌙 Имя",
            placeholder="Введите имя...",
            default=application_data.get('Имя', ''),
            required=True,
            max_length=100
        )
        self.add_item(self.name_input)
        
        self.age_input = TextInput(
            label="🎂 Возраст",
            placeholder="Введите возраст...",
            default=application_data.get('Возраст', ''),
            required=True,
            max_length=20
        )
        self.add_item(self.age_input)
        
        self.about_input = TextInput(
            label="💫 О себе",
            placeholder="Расскажите о себе...",
            default=application_data.get('О себе', ''),
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        )
        self.add_item(self.about_input)
        
        self.search_input = TextInput(
            label="🌸 Кого ищу",
            placeholder="Кого вы ищете?",
            default=application_data.get('Кого ищу', ''),
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        self.add_item(self.search_input)
        
        self.wish_input = TextInput(
            label="📜 Пожелание",
            placeholder="Ваше пожелание...",
            default=application_data.get('Пожелание', ''),
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=500
        )
        self.add_item(self.wish_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.application_data['Имя'] = self.name_input.value
            self.application_data['Возраст'] = self.age_input.value
            self.application_data['О себе'] = self.about_input.value
            self.application_data['Кого ищу'] = self.search_input.value
            self.application_data['Пожелание'] = self.wish_input.value
            
            embed = self.parent_view.create_embed(self.application_data, self.user_id)
            await self.original_message.edit(embed=embed)
            
            if hasattr(self.parent_view, 'application_id'):
                data = load_applications_data()
                app_id = str(self.parent_view.application_id)
                if app_id in data["applications"]:
                    data["applications"][app_id]["content"] = self.application_data
                    save_applications_data(data)
            
            await interaction.response.send_message("✅ Заявка успешно отредактирована!", ephemeral=True)
        except Exception as e:
            print(f"❌ Ошибка редактирования: {e}")
            await interaction.response.send_message("❌ Ошибка при редактировании!", ephemeral=True)

# ==================== КЛАСС ДЛЯ КНОПОК МОДЕРАЦИИ ====================

class ModerationButtons(View):
    def __init__(self, user_id, username, user_discriminator, original_content, channel_id, application_id=None):
        super().__init__(timeout=86400)
        self.user_id = user_id
        self.username = username
        self.user_discriminator = user_discriminator
        self.original_content = original_content
        self.channel_id = channel_id
        self.decision_made = False
        self.application_data = original_content.copy()
        self.moderation_message = None
        self.application_id = application_id or f"{user_id}_{int(datetime.now().timestamp())}"
    
    def create_embed(self, data, user_id=None):
        embed = discord.Embed(
            title="📝 Новая заявка на модерацию",
            description=f"Заявка от пользователя <@{user_id or self.user_id}> требует проверки",
            color=discord.Color.gold()
        )
        embed.add_field(name="👤 Пользователь", value=f"<@{user_id or self.user_id}>\n{self.username}", inline=True)
        embed.add_field(name="🆔 ID", value=str(user_id or self.user_id), inline=True)
        
        content_text = ""
        for key, value in data.items():
            content_text += f"**{key}:** {value}\n"
        
        if content_text:
            embed.add_field(name="📝 Содержание заявки", value=content_text[:1000], inline=False)
        
        embed.set_footer(text="Нажмите кнопку ниже, чтобы одобрить, отклонить или отредактировать заявку")
        embed.timestamp = discord.utils.utcnow()
        return embed
    
    def get_formatted_content(self):
        return (f"🌙 Имя: {self.application_data.get('Имя', 'Не указано')}\n"
                f"🎂 Возраст: {self.application_data.get('Возраст', 'Не указан')}\n"
                f"💫 О себе: {self.application_data.get('О себе', 'Не указано')}\n"
                f"🌸 Кого ищу: {self.application_data.get('Кого ищу', 'Не указано')}\n"
                f"📜 Пожелание: {self.application_data.get('Пожелание', 'Не указано')}")
    
    def get_final_content(self):
        return (f"👤 **Автор заявки:** <@{self.user_id}>\n\n"
                f"🌙 Имя: {self.application_data.get('Имя', 'Не указано')}\n"
                f"🎂 Возраст: {self.application_data.get('Возраст', 'Не указан')}\n"
                f"💫 О себе: {self.application_data.get('О себе', 'Не указано')}\n"
                f"🌸 Кого ищу: {self.application_data.get('Кого ищу', 'Не указано')}\n"
                f"📜 Пожелание: {self.application_data.get('Пожелание', 'Не указано')}")
    
    @discord.ui.button(label='✅ Одобрить', style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        if self.decision_made:
            await interaction.response.send_message("❌ Решение по этой заявке уже принято!", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ У вас нет прав для этого!", ephemeral=True)
            return
        
        self.decision_made = True
        
        try:
            channel = bot.get_channel(self.channel_id)
            if channel:
                save_application(
                    self.application_id,
                    self.user_id,
                    self.username,
                    self.application_data,
                    interaction.user.id,
                    datetime.now().isoformat()
                )
                
                chat_buttons = ChatButtons(self.application_id, self.user_id)
                final_message = await channel.send(
                    self.get_final_content(),
                    view=chat_buttons
                )
                update_application_message_id(self.application_id, final_message.id)
                await final_message.add_reaction("✅")
                
                embed = discord.Embed(
                    title="✅ ЗАЯВКА ОДОБРЕНА",
                    description=f"Заявка пользователя <@{self.user_id}> была одобрена",
                    color=discord.Color.green()
                )
                embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
                embed.add_field(name="ID пользователя", value=str(self.user_id), inline=True)
                embed.add_field(name="Сохранено", value=f"ID заявки: `{self.application_id}`", inline=True)
                embed.add_field(name="Заявка", value=f"```\n{self.get_formatted_content()}\n```", inline=False)
                await interaction.message.edit(embed=embed, view=None)
                
                try:
                    user = await bot.fetch_user(self.user_id)
                    if user:
                        embed_user = discord.Embed(
                            title="✅ Ваша заявка одобрена!",
                            description="Ваша заявка в канале знакомств была одобрена модерацией и опубликована!",
                            color=discord.Color.green()
                        )
                        embed_user.add_field(
                            name="📌 Ваша заявка:",
                            value=f"```\n{self.get_formatted_content()}\n```",
                            inline=False
                        )
                        embed_user.add_field(
                            name="💬 Как это работает:",
                            value="Когда кто-то захочет начать чат, он нажмет кнопку **'Начать чат'** под вашей заявкой.\n\n"
                                  "📊 **Ограничения:**\n"
                                  "• Одновременно может быть до 3 активных чатов\n"
                                  "• При попытке начать 2-й чат, вам будет отправлен запрос на разрешение\n"
                                  "• Вы можете выбрать анонимный или открытый режим чата\n"
                                  "• После завершения чата, история сохраняется в архиве\n\n"
                                  "**Внимание!** Диалог приватный - только вы и ваш собеседник видите канал.",
                            inline=False
                        )
                        await user.send(embed=embed_user)
                except Exception as e:
                    print(f"Ошибка отправки уведомления пользователю: {e}")
                
                await interaction.response.send_message("✅ Заявка одобрена и опубликована!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Канал не найден!", ephemeral=True)
        except Exception as e:
            print(f"❌ Ошибка одобрения: {e}")
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)
    
    @discord.ui.button(label='✏️ Редактировать', style=discord.ButtonStyle.primary)
    async def edit_button(self, interaction: discord.Interaction, button: Button):
        if self.decision_made:
            await interaction.response.send_message("❌ Решение по этой заявке уже принято!", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ У вас нет прав для этого!", ephemeral=True)
            return
        
        self.moderation_message = interaction.message
        modal = EditApplicationModal(self.application_data, interaction.message, self, self.user_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='❌ Отклонить', style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: Button):
        if self.decision_made:
            await interaction.response.send_message("❌ Решение по этой заявке уже принято!", ephemeral=True)
            return
        
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ У вас нет прав для этого!", ephemeral=True)
            return
        
        self.decision_made = True
        
        embed = discord.Embed(
            title="❌ ЗАЯВКА ОТКЛОНЕНА",
            description=f"Заявка пользователя <@{self.user_id}> была отклонена",
            color=discord.Color.red()
        )
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="ID пользователя", value=str(self.user_id), inline=True)
        embed.add_field(name="Заявка", value=f"```\n{self.get_formatted_content()}\n```", inline=False)
        await interaction.message.edit(embed=embed, view=None)
        
        delete_application(self.application_id)
        
        try:
            user = await bot.fetch_user(self.user_id)
            if user:
                embed_user = discord.Embed(
                    title="❌ Ваша заявка была отклонена",
                    description="К сожалению, ваша заявка в канале знакомств была отклонена модерацией.",
                    color=discord.Color.red()
                )
                embed_user.add_field(
                    name="📝 Правильный формат заявки:",
                    value="🌙 Имя: <ваше имя>\n"
                          "🎂 Возраст: <ваш возраст>\n"
                          "💫 О себе (характер, увлечения): <описание>\n"
                          "🌸 Кого ищу: <кого вы ищете>\n"
                          "📜 Пожелание/послание: <ваше пожелание>",
                    inline=False
                )
                embed_user.set_footer(text="Пожалуйста, оформите заявку правильно и отправьте заново.")
                await user.send(embed=embed_user)
        except:
            pass
        
        await interaction.response.send_message("❌ Заявка отклонена!", ephemeral=True)

# ==================== ФУНКЦИИ РАБОТЫ С РОЛЯМИ ====================

async def find_or_create_role(guild, role_name, color):
    try:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            return role
        
        for r in guild.roles:
            if role_name.lower() in r.name.lower():
                return r
        
        new_role = await guild.create_role(
            name=role_name,
            color=color,
            mentionable=True,
            reason="Автоматическое создание роли ботом"
        )
        print(f"✅ Создана роль: {new_role.name}")
        return new_role
    except Exception as e:
        print(f"❌ Ошибка создания роли {role_name}: {e}")
        return None

async def assign_newbie_role(member):
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
    try:
        role_variations = [
            "🌸・Странник",
            "Странник",
            "странник",
            "🌸・странник",
            "Китайский младший",
            "китайский младший",
            "Китайский Младший"
        ]
        
        found_role = None
        for variation in role_variations:
            role = discord.utils.get(member.guild.roles, name=variation)
            if role:
                found_role = role
                print(f"🔍 Найдена роль: {role.name}")
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
            
            found_role = await member.guild.create_role(
                name=MAIN_ROLE_NAME,
                color=discord.Color.blue(),
                permissions=permissions,
                mentionable=True,
                reason="Автоматическое создание основной роли ботом"
            )
            print(f"✅ Создана основная роль: {found_role.name}")
        
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
    try:
        role_variations = [
            "🌸・Странник",
            "Странник",
            "странник",
            "🌸・странник",
            "Китайский младший",
            "китайский младший",
            "Китайский Младший"
        ]
        
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
    if not gender:
        return None
        
    if gender == 'male':
        role_name = 'Воин'
        color = GENDER_COLORS['male']
        opposite = ['Цветок', 'Женщина', 'Ж', 'Жен', 'Female', 'Woman', 'Девушка']
    else:
        role_name = 'Цветок'
        color = GENDER_COLORS['female']
        opposite = ['Воин', 'Мужчина', 'М', 'Муж', 'Male', 'Man', 'Парень']
    
    try:
        role = await find_or_create_role(member.guild, role_name, color)
        if not role:
            return None
        
        for opp_name in opposite:
            opp_role = discord.utils.get(member.guild.roles, name=opp_name)
            if opp_role and opp_role in member.roles:
                await member.remove_roles(opp_role)
        
        if role not in member.roles:
            await member.add_roles(role)
            print(f"✅ Назначена роль: {role.name} -> {member.name}")
        
        return role
        
    except Exception as e:
        print(f"❌ Ошибка назначения гендерной роли: {e}")
        return None

async def assign_age_role(member, age):
    if not age:
        return None
        
    role_name = age
    color = AGE_COLORS.get(age, discord.Color.default())
    
    try:
        role = await find_or_create_role(member.guild, role_name, color)
        if not role:
            return None
        
        for age_key in AGE_COLORS.keys():
            if age_key != age:
                old_role = discord.utils.get(member.guild.roles, name=age_key)
                if old_role and old_role in member.roles:
                    await member.remove_roles(old_role)
        
        if role not in member.roles:
            await member.add_roles(role)
            print(f"✅ Назначена роль: {role.name} -> {member.name}")
        
        return role
        
    except Exception as e:
        print(f"❌ Ошибка назначения возрастной роли: {e}")
        return None

async def assign_game_roles(member, games):
    if not games:
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

# ==================== ФУНКЦИИ ЛОГИРОВАНИЯ ====================

async def send_registration_log(member):
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="✅ Новая регистрация",
                description=f"{member.mention} прошёл полную регистрацию!",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Пользователь", value=member.name, inline=True)
            embed.add_field(name="🆔 ID", value=member.id, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Ошибка логирования: {e}")

async def send_role_change_log(member, changes):
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel and changes:
            embed = discord.Embed(
                title="🔄 Изменение ролей",
                description=f"{member.mention} изменил свои роли",
                color=discord.Color.blue()
            )
            embed.add_field(name="📋 Изменения", value='\n'.join(changes), inline=False)
            embed.set_footer(text=f"ID: {member.id}")
            await channel.send(embed=embed)
    except Exception as e:
        print(f"❌ Ошибка логирования: {e}")

# ==================== ОТПРАВКА НА МОДЕРАЦИЮ ====================

async def send_to_moderation(message):
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        
        content = message.content
        fields = {}
        
        name_match = re.search(r'🌙 Имя:\s*(.+?)(?=\n|$)', content)
        age_match = re.search(r'🎂 Возраст:\s*(.+?)(?=\n|$)', content)
        about_match = re.search(r'💫 О себе\s*(.+?)(?=\n🌸|$)', content, re.DOTALL)
        search_match = re.search(r'🌸 Кого ищу:\s*(.+?)(?=\n📜|$)', content, re.DOTALL)
        wish_match = re.search(r'📜 Пожелание/послание:\s*(.+?)(?=\n|$)', content, re.DOTALL)
        
        if name_match:
            fields['Имя'] = name_match.group(1).strip()
        if age_match:
            fields['Возраст'] = age_match.group(1).strip()
        if about_match:
            fields['О себе'] = about_match.group(1).strip()
        if search_match:
            fields['Кого ищу'] = search_match.group(1).strip()
        if wish_match:
            fields['Пожелание'] = wish_match.group(1).strip()
        
        application_id = f"{message.author.id}_{int(datetime.now().timestamp())}"
        
        view = ModerationButtons(
            user_id=message.author.id,
            username=message.author.name,
            user_discriminator=message.author.discriminator,
            original_content=fields,
            channel_id=message.channel.id,
            application_id=application_id
        )
        
        embed = view.create_embed(fields, message.author.id)
        await channel.send(embed=embed, view=view)
    except Exception as e:
        print(f"❌ Ошибка отправки на модерацию: {e}")

# ==================== ПРОВЕРКА ЗАЯВОК ====================

async def moderate_existing_messages(channel):
    if not channel:
        return
    
    print(f"🔍 Начинаю проверку существующих сообщений в канале {channel.name}...")
    
    to_moderation_count = 0
    fixed_messages = 0
    
    try:
        async for message in channel.history(limit=1000):
            if message.author == bot.user:
                if not message.components or len(message.components) == 0:
                    if "Автор заявки:" in message.content:
                        author_match = re.search(r'Автор заявки: <@!?(\d+)>', message.content)
                        if author_match:
                            author_id = author_match.group(1)
                            data = load_applications_data()
                            app_id = None
                            for aid, app in data["applications"].items():
                                if str(app.get("user_id")) == str(author_id) and str(app.get("message_id")) == str(message.id):
                                    app_id = aid
                                    break
                            
                            if not app_id:
                                app_id = f"fixed_{message.id}"
                                save_application(
                                    app_id,
                                    author_id,
                                    "Пользователь",
                                    {"Имя": "Восстановлено", "Возраст": "?", "О себе": "?", "Кого ищу": "?", "Пожелание": "?"},
                                    None,
                                    datetime.now().isoformat()
                                )
                            
                            chat_buttons = ChatButtons(app_id, author_id, message.id)
                            try:
                                await message.edit(view=chat_buttons)
                                fixed_messages += 1
                                print(f"✅ Добавлены кнопки к сообщению {message.id}")
                                await asyncio.sleep(0.5)
                            except Exception as e:
                                print(f"❌ Ошибка добавления кнопок: {e}")
            
            elif message.author.bot:
                continue
            
            else:
                has_required_fields = all([
                    '🌙 Имя:' in message.content,
                    '🎂 Возраст:' in message.content,
                    '💫 О себе' in message.content,
                    '🌸 Кого ищу:' in message.content,
                    '📜 Пожелание/послание:' in message.content
                ])
                
                if has_required_fields:
                    try:
                        await message.delete()
                        await send_to_moderation(message)
                        to_moderation_count += 1
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"❌ Ошибка при отправке на модерацию: {e}")
        
        print(f"✅ Проверка завершена! Отправлено на модерацию: {to_moderation_count}, Исправлено сообщений: {fixed_messages}")
        
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="📋 Отчет о модерации",
                description=f"Проверка сообщений в канале {channel.mention}",
                color=discord.Color.blue()
            )
            embed.add_field(name="🔍 Отправлено на модерацию", value=str(to_moderation_count), inline=True)
            embed.add_field(name="🔧 Исправлено сообщений", value=str(fixed_messages), inline=True)
            await log_channel.send(embed=embed)
            
    except Exception as e:
        print(f"❌ Критическая ошибка при модерации: {e}")

# ==================== ПРОВЕРКА НОВЫХ ЗАЯВОК ====================

@bot.event
async def on_message(message):
    try:
        if message.author.bot:
            await bot.process_commands(message)
            return
        
        if not isinstance(message.channel, discord.TextChannel):
            await bot.process_commands(message)
            return
        
        if message.channel.name == DATING_CHANNEL_NAME:
            has_required_fields = all([
                '🌙 Имя:' in message.content,
                '🎂 Возраст:' in message.content,
                '💫 О себе' in message.content,
                '🌸 Кого ищу:' in message.content,
                '📜 Пожелание/послание:' in message.content
            ])
            
            if has_required_fields:
                try:
                    await message.delete()
                    await send_to_moderation(message)
                    
                    embed = discord.Embed(
                        title="🔍 Заявка отправлена на модерацию",
                        description="Ваша заявка отправлена на проверку модераторам. Ожидайте решения.",
                        color=discord.Color.gold()
                    )
                    embed.add_field(
                        name="⏰ Время ожидания",
                        value="Обычно это занимает не более 24 часов.",
                        inline=False
                    )
                    try:
                        await message.author.send(embed=embed)
                    except:
                        await message.channel.send(
                            f"{message.author.mention}, ваша заявка отправлена на модерацию! Ожидайте решения.",
                            delete_after=30
                        )
                    return
                except Exception as e:
                    print(f"Ошибка при отправке на модерацию: {e}")
            else:
                try:
                    await message.delete()
                    embed = discord.Embed(
                        title="❌ Заявка удалена",
                        description="Ваша заявка не содержит всех необходимых полей.",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="📝 Правильный формат:",
                        value="🌙 Имя: <ваше имя>\n"
                              "🎂 Возраст: <ваш возраст>\n"
                              "💫 О себе (характер, увлечения): <описание>\n"
                              "🌸 Кого ищу: <кого вы ищете>\n"
                              "📜 Пожелание/послание: <ваше пожелание>",
                        inline=False
                    )
                    try:
                        await message.author.send(embed=embed)
                    except:
                        await message.channel.send(
                            f"{message.author.mention}, ваша заявка удалена - не все поля заполнены!",
                            delete_after=30
                        )
                    return
                except:
                    pass
        
        await bot.process_commands(message)
    except Exception as e:
        print(f"❌ Ошибка в on_message: {e}")

# ==================== ОБРАБОТЧИК ОШИБОК ====================

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
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
            
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
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
        except Exception as e:
            print(f"❌ Ошибка в обработчике ошибок: {e}")

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        try:
            error_msg = f"Ошибка в событии {event}:\n{traceback.format_exc()}"
            logging.error(error_msg)
            
            log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
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
        except Exception as e:
            print(f"❌ Ошибка в обработчике ошибок: {e}")

bot.add_cog(ErrorHandler(bot))

# ==================== ЭМОДЗИ ====================

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
    'confetti': '🎊',
    'moon': '🌙'
}

GENDER_COLORS = {
    'male': discord.Color.blue(),
    'female': discord.Color.magenta()
}

AGE_COLORS = {
    'Меньше 16 лет': discord.Color.from_rgb(255, 182, 193),
    '16-17 лет': discord.Color.from_rgb(144, 238, 144),
    '18-24 лет': discord.Color.from_rgb(60, 179, 113),
    '25-29 лет': discord.Color.from_rgb(255, 165, 0),
    '30+ лет': discord.Color.from_rgb(218, 165, 32)
}

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

# ==================== ФУНКЦИЯ СОЗДАНИЯ ПРИВЕТСТВЕННОГО СООБЩЕНИЯ ====================

async def create_welcome_message(channel, guild):
    try:
        print(f"🗑️ Очищаю канал {channel.name}...")
        async for message in channel.history(limit=1000):
            try:
                await message.delete()
                await asyncio.sleep(0.3)
            except:
                pass
        print(f"✅ Канал {channel.name} очищен")
    except Exception as e:
        print(f"❌ Ошибка при очистке канала: {e}")
    
    style_name = get_welcome_style()
    style = WELCOME_STYLES.get(style_name, WELCOME_STYLES["modern"])
    
    embed = discord.Embed(
        title=style["title"],
        description=style["description"].replace("{role}", NEWBIE_ROLE_NAME),
        color=discord.Color.from_rgb(*style["color"])
    )
    
    if guild and guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.set_footer(text=style["footer"])
    
    view = ApplyView()
    await channel.send(embed=embed, view=view)
    print(f"✅ Приветственное сообщение обновлено (стиль: {style['name']})")

# ==================== КЛАССЫ ИНТЕРФЕЙСА ====================

class ApplyView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='📝 Пройти регистрацию', style=discord.ButtonStyle.success, custom_id='apply_button')
    async def apply_button(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            member = await interaction.guild.fetch_member(interaction.user.id)
            user_data = {'member': member, 'guild': interaction.guild, 'from_registration': True}
            
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
                description=f"{EMOJIS['star']} Кто вы?\n\n"
                           f"👨 **Мужчина** (роль **Воин**)\n"
                           f"👩 **Женщина** (роль **Цветок**)",
                color=discord.Color.blue()
            )
            gender_embed.set_footer(text="Нажмите на одну из кнопок ниже")
            
            view = GenderView(user_data, from_registration=True)
            await interaction.user.send(embed=welcome_embed)
            await interaction.user.send(embed=gender_embed, view=view)
            await interaction.followup.send(f"{EMOJIS['rocket']} Проверь личные сообщения!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Откройте личные сообщения в настройках Discord!", ephemeral=True)
        except Exception as e:
            print(f"Ошибка в apply_button: {e}")
            await interaction.followup.send("❌ Произошла ошибка. Попробуйте позже.", ephemeral=True)

class GenderView(View):
    def __init__(self, user_data, from_registration=True):
        super().__init__(timeout=300)
        self.user_data = user_data
        self.from_registration = from_registration
        
    @discord.ui.button(label='Я мужчина (Воин)', style=discord.ButtonStyle.primary, emoji='👨')
    async def male_button(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            self.user_data['gender'] = 'male'
            
            if self.from_registration:
                await interaction.followup.send(f"{EMOJIS['male']} Отлично! Вы выбрали: **Мужчина (Воин)**", ephemeral=True)
                await show_age_selection(interaction, self.user_data, self.from_registration)
            else:
                member = self.user_data['member']
                await assign_gender_role(member, 'male')
                await interaction.followup.send(f"{EMOJIS['male']} Пол обновлён: **Мужчина (Воин)**", ephemeral=True)
                await send_role_change_log(member, [f"{EMOJIS['gender']} Пол: 👨 Мужчина (Воин)"])
            
            self.stop()
        except Exception as e:
            print(f"❌ Ошибка в male_button: {e}")
            await interaction.followup.send("❌ Произошла ошибка.", ephemeral=True)
        
    @discord.ui.button(label='Я женщина (Цветок)', style=discord.ButtonStyle.primary, emoji='👩')
    async def female_button(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            self.user_data['gender'] = 'female'
            
            if self.from_registration:
                await interaction.followup.send(f"{EMOJIS['female']} Прекрасно! Вы выбрали: **Женщина (Цветок)**", ephemeral=True)
                await show_age_selection(interaction, self.user_data, self.from_registration)
            else:
                member = self.user_data['member']
                await assign_gender_role(member, 'female')
                await interaction.followup.send(f"{EMOJIS['female']} Пол обновлён: **Женщина (Цветок)**", ephemeral=True)
                await send_role_change_log(member, [f"{EMOJIS['gender']} Пол: 👩 Женщина (Цветок)"])
            
            self.stop()
        except Exception as e:
            print(f"❌ Ошибка в female_button: {e}")
            await interaction.followup.send("❌ Произошла ошибка.", ephemeral=True)

class AgeView(View):
    def __init__(self, user_data, from_registration=True):
        super().__init__(timeout=300)
        self.user_data = user_data
        self.from_registration = from_registration
        
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
            try:
                await interaction.response.defer()
                clean_age = age.replace('🍼 ', '').replace('🌱 ', '').replace('🌿 ', '').replace('🌳 ', '').replace('🍂 ', '')
                self.user_data['age'] = clean_age
                
                if self.from_registration:
                    await interaction.followup.send(f"{EMOJIS['age']} Принято! Ваш возраст: **{clean_age}**", ephemeral=True)
                    await show_games_selection(interaction, self.user_data, self.from_registration)
                else:
                    member = self.user_data['member']
                    await assign_age_role(member, clean_age)
                    await interaction.followup.send(f"{EMOJIS['age']} Возраст обновлён: **{clean_age}**", ephemeral=True)
                    await send_role_change_log(member, [f"{EMOJIS['age']} Возраст: {clean_age}"])
                
                self.stop()
            except Exception as e:
                print(f"❌ Ошибка в age_callback: {e}")
                await interaction.followup.send("❌ Произошла ошибка.", ephemeral=True)
        return callback

class GamesSelect(Select):
    def __init__(self, user_data, from_registration=True):
        self.user_data = user_data
        self.from_registration = from_registration
        
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
        try:
            await interaction.response.defer()
            self.user_data['games'] = self.values
            
            if self.from_registration:
                await complete_registration(interaction, self.user_data)
            else:
                await update_roles_only(interaction, self.user_data)
            
            self.view.stop()
        except Exception as e:
            print(f"❌ Ошибка в games callback: {e}")
            await interaction.followup.send("❌ Произошла ошибка.", ephemeral=True)

class GamesView(View):
    def __init__(self, user_data, from_registration=True):
        super().__init__(timeout=300)
        self.user_data = user_data
        self.from_registration = from_registration
        self.add_item(GamesSelect(user_data, from_registration))

class ChangeGamesView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='🎮 Сменить игры', style=discord.ButtonStyle.primary, custom_id='change_games')
    async def change_games(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            member = await interaction.guild.fetch_member(interaction.user.id)
            user_data = {'member': member, 'guild': interaction.guild, 'from_registration': False}
            
            embed = discord.Embed(
                title=f"{EMOJIS['games']} Выберите ваши любимые игры",
                description=f"{EMOJIS['sparkles']} Во что вы сейчас играете?\nВы можете выбрать несколько вариантов!",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Старые игровые роли будут заменены")
            
            view = GamesView(user_data, from_registration=False)
            await interaction.user.send(embed=embed, view=view)
            await interaction.followup.send(f"{EMOJIS['rocket']} Проверь личные сообщения!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Откройте личные сообщения!", ephemeral=True)
        except Exception as e:
            print(f"❌ Ошибка в change_games: {e}")
            await interaction.followup.send("❌ Произошла ошибка.", ephemeral=True)
    
    @discord.ui.button(label='👤 Указать пол (если нет)', style=discord.ButtonStyle.secondary, custom_id='add_gender')
    async def add_gender(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            member = await interaction.guild.fetch_member(interaction.user.id)
            
            has_gender = False
            for role in member.roles:
                if role.name.lower() in ['воин', 'цветок', 'мужчина', 'женщина', 'м', 'ж', 'male', 'female', 'man', 'woman', 'парень', 'девушка']:
                    has_gender = True
                    break
            
            if has_gender:
                await interaction.followup.send("❌ У вас уже указан пол. Обратитесь к администратору для смены.", ephemeral=True)
                return
            
            user_data = {'member': member, 'guild': interaction.guild, 'from_registration': False}
            
            embed = discord.Embed(
                title=f"{EMOJIS['gender']} Выберите свой пол",
                description=f"{EMOJIS['star']} Кто вы?\n\n"
                           f"👨 **Мужчина** (роль **Воин**)\n"
                           f"👩 **Женщина** (роль **Цветок**)",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Пол можно указать только один раз")
            
            view = GenderView(user_data, from_registration=False)
            await interaction.user.send(embed=embed, view=view)
            await interaction.followup.send(f"{EMOJIS['rocket']} Проверь личные сообщения!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Откройте личные сообщения!", ephemeral=True)
        except Exception as e:
            print(f"❌ Ошибка в add_gender: {e}")
            await interaction.followup.send("❌ Произошла ошибка.", ephemeral=True)
    
    @discord.ui.button(label='🎂 Указать возраст (если нет)', style=discord.ButtonStyle.secondary, custom_id='add_age')
    async def add_age(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.defer()
            member = await interaction.guild.fetch_member(interaction.user.id)
            
            has_age = False
            for age_key in AGE_COLORS.keys():
                if discord.utils.get(member.roles, name=age_key):
                    has_age = True
                    break
            
            if has_age:
                await interaction.followup.send("❌ У вас уже указан возраст. Обратитесь к администратору для смены.", ephemeral=True)
                return
            
            user_data = {'member': member, 'guild': interaction.guild, 'from_registration': False}
            
            embed = discord.Embed(
                title=f"{EMOJIS['age']} Выберите ваш возраст",
                description=f"{EMOJIS['star']} К какой возрастной категории вы относитесь?",
                color=discord.Color.green()
            )
            embed.set_footer(text="Возраст можно указать только один раз")
            
            view = AgeView(user_data, from_registration=False)
            await interaction.user.send(embed=embed, view=view)
            await interaction.followup.send(f"{EMOJIS['rocket']} Проверь личные сообщения!", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Откройте личные сообщения!", ephemeral=True)
        except Exception as e:
            print(f"❌ Ошибка в add_age: {e}")
            await interaction.followup.send("❌ Произошла ошибка.", ephemeral=True)

# ==================== ФУНКЦИИ ПОКАЗА ВОПРОСОВ ====================

async def show_age_selection(interaction: discord.Interaction, user_data, from_registration=True):
    try:
        embed = discord.Embed(
            title=f"{EMOJIS['age']} Вопрос 2 из 3: Выберите ваш возраст",
            description=f"{EMOJIS['star']} К какой возрастной категории вы относитесь?",
            color=discord.Color.green()
        )
        embed.set_footer(text="Выберите один из вариантов ниже")
        
        view = AgeView(user_data, from_registration)
        await interaction.user.send(embed=embed, view=view)
    except Exception as e:
        print(f"❌ Ошибка в show_age_selection: {e}")

async def show_games_selection(interaction: discord.Interaction, user_data, from_registration=True):
    try:
        embed = discord.Embed(
            title=f"{EMOJIS['games']} Вопрос 3 из 3: Выберите ваши любимые игры",
            description=f"{EMOJIS['sparkles']} Во что вы любите играть?\nВы можете выбрать несколько вариантов!",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Выберите одну или несколько игр из списка")
        
        view = GamesView(user_data, from_registration)
        await interaction.user.send(embed=embed, view=view)
    except Exception as e:
        print(f"❌ Ошибка в show_games_selection: {e}")

# ==================== ЗАВЕРШЕНИЕ РЕГИСТРАЦИИ ====================

async def complete_registration(interaction: discord.Interaction, user_data):
    try:
        member = user_data['member']
        from_registration = user_data.get('from_registration', True)
        
        complete_embed = discord.Embed(
            title=f"{EMOJIS['complete']} Регистрация завершена!",
            description=f"{EMOJIS['party']} Поздравляем, {member.name}!",
            color=discord.Color.teal()
        )
        
        if user_data.get('gender') == 'male':
            gender_display = "👨 Мужчина (Воин)"
        elif user_data.get('gender') == 'female':
            gender_display = "👩 Женщина (Цветок)"
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
        
        await remove_newbie_role(member)
        await assign_main_role(member)
        
        await asyncio.sleep(1)
        
        if from_registration:
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
            await send_registration_log(member)
    except Exception as e:
        print(f"❌ Ошибка в complete_registration: {e}")

async def update_roles_only(interaction: discord.Interaction, user_data):
    try:
        member = user_data['member']
        changes = []
        
        if user_data.get('gender'):
            await assign_gender_role(member, user_data['gender'])
            gender_display = "👨 Мужчина (Воин)" if user_data['gender'] == 'male' else "👩 Женщина (Цветок)"
            changes.append(f"{EMOJIS['gender']} Пол: {gender_display}")
        
        if user_data.get('age'):
            await assign_age_role(member, user_data['age'])
            changes.append(f"{EMOJIS['age']} Возраст: {user_data['age']}")
        
        if user_data.get('games'):
            await assign_game_roles(member, user_data['games'])
            changes.append(f"{EMOJIS['games']} Игры: {', '.join(user_data['games'])}")
        
        await interaction.user.send("✅ Ваши роли успешно обновлены!")
        
        if changes:
            await send_role_change_log(member, changes)
    except Exception as e:
        print(f"❌ Ошибка в update_roles_only: {e}")

# ==================== КОМАНДЫ БОТА ====================

@bot.command(name='update_roles')
async def update_roles(ctx):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        member = ctx.author
        
        has_newbie = False
        for role in member.roles:
            if role.name == NEWBIE_ROLE_NAME:
                has_newbie = True
                break
        
        if has_newbie:
            await ctx.send("❌ Вы не можете менять роли, пока не пройдете регистрацию!")
            return
        
        embed = discord.Embed(
            title=f"{EMOJIS['sparkles']} Изменение ролей",
            description=f"{EMOJIS['star']} {ctx.author.mention}, вы можете изменить свои роли!\n\n"
                       f"📌 **Что можно изменить:**\n"
                       f"• 🎮 **Игры** - выберите свои любимые игры\n"
                       f"• 👤 **Пол** - укажите, если не указан\n"
                       f"• 🎂 **Возраст** - укажите, если не указан\n\n"
                       f"⚠️ **Важно:** Некоторые роли можно изменить только через администратора.",
            color=discord.Color.blue()
        )
        
        view = ChangeGamesView()
        await ctx.send(embed=embed, view=view)
        
    except Exception as e:
        print(f"❌ Ошибка в update_roles: {e}")
        await ctx.send(f"❌ Ошибка: {e}")

@bot.command(name='list_chats')
async def list_chats(ctx):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        user_chats = ChatManager.get_active_chats_for_user(ctx.author.id)
        
        if not user_chats:
            await ctx.send("📭 У вас нет активных диалогов.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💬 Ваши активные диалоги",
            description=f"Всего диалогов: {len(user_chats)}",
            color=discord.Color.blue()
        )
        
        for i, (chat_id, chat) in enumerate(user_chats[:10], 1):
            other_user_id = chat.get("from_user_id") if str(chat.get("to_user_id")) == str(ctx.author.id) else chat.get("to_user_id")
            
            try:
                other_user = await bot.fetch_user(int(other_user_id))
                username = other_user.name if other_user else "Неизвестно"
            except:
                username = "Неизвестно"
            
            data = load_applications_data()
            app_data = data["applications"].get(chat.get("application_id", ""), {})
            app_content = app_data.get("content", {})
            
            channel_id = chat.get("channel_id")
            channel_info = ""
            if channel_id:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    channel_info = f"**Канал:** {channel.mention}"
                else:
                    channel_info = "**Канал:** удален"
            
            is_anonymous = chat.get("is_anonymous", False)
            
            embed.add_field(
                name=f"📌 Диалог #{i}",
                value=f"**Собеседник:** {username}\n"
                      f"**Заявка:** {app_content.get('Имя', 'Неизвестно')}\n"
                      f"**Режим:** {'Анонимный' if is_anonymous else 'Открытый'}\n"
                      f"**Начат:** {chat.get('started_at', '')[:16]}\n"
                      f"{channel_info}\n"
                      f"**Сообщений:** {len(chat.get('messages', []))}",
                inline=False
            )
        
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"❌ Ошибка в list_chats: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='clear_chat')
async def clear_chat(ctx, application_id: str = None):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        if not application_id:
            await ctx.send("❌ Укажите ID заявки! Используйте `!list_chats` для просмотра.")
            return
        
        active_chats = ChatManager.get_active_chat_for_application(application_id)
        if not active_chats:
            await ctx.send("❌ Активный диалог для этой заявки не найден!")
            return
        
        chat_id = None
        chat = None
        for cid, c in active_chats:
            if ChatManager.is_user_in_chat(ctx.author.id, cid):
                chat_id = cid
                chat = c
                break
        
        if not chat:
            await ctx.send("❌ Вы не участвуете в этом диалоге!")
            return
        
        channel_id = chat.get("channel_id")
        if channel_id:
            channel = bot.get_channel(int(channel_id))
            if channel:
                await TemporaryChannelManager.delete_channel(channel)
        
        if ChatManager.end_chat(chat_id):
            other_user_id = ChatManager.get_other_user(chat_id, ctx.author.id)
            if other_user_id:
                try:
                    other_user = await bot.fetch_user(int(other_user_id))
                    if other_user:
                        embed = discord.Embed(
                            title="🛑 Диалог завершен",
                            description="Ваш собеседник завершил диалог.",
                            color=discord.Color.red()
                        )
                        await other_user.send(embed=embed)
                except:
                    pass
            
            await ctx.send("✅ Диалог успешно завершен!", ephemeral=True)
        else:
            await ctx.send("❌ Ошибка при завершении диалога!", ephemeral=True)
    except Exception as e:
        print(f"❌ Ошибка в clear_chat: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='block')
async def block_user_cmd(ctx, user_id: str = None):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        if not user_id:
            await ctx.send("❌ Укажите ID пользователя для блокировки!")
            return
        
        user_to_block = int(user_id)
        
        if str(ctx.author.id) == user_id:
            await ctx.send("❌ Вы не можете заблокировать себя!")
            return
        
        if block_user(ctx.author.id, user_to_block):
            await ctx.send(f"✅ Пользователь <@{user_id}> заблокирован!", ephemeral=True)
            
            user_chats = ChatManager.get_active_chats_for_user(ctx.author.id)
            for chat_id, chat in user_chats:
                other_user = ChatManager.get_other_user(chat_id, ctx.author.id)
                if other_user and str(other_user) == user_id:
                    ChatManager.end_chat(chat_id)
                    
                    channel_id = chat.get("channel_id")
                    if channel_id:
                        channel = bot.get_channel(int(channel_id))
                        if channel:
                            await TemporaryChannelManager.delete_channel(channel)
                    
                    try:
                        other_user_obj = await bot.fetch_user(int(other_user))
                        if other_user_obj:
                            embed = discord.Embed(
                                title="🚫 Вы были заблокированы",
                                description="Пользователь заблокировал вас. Диалог завершен.",
                                color=discord.Color.red()
                            )
                            await other_user_obj.send(embed=embed)
                    except:
                        pass
        else:
            await ctx.send("❌ Пользователь уже заблокирован!", ephemeral=True)
            
    except ValueError:
        await ctx.send("❌ Укажите корректный ID пользователя!")
    except Exception as e:
        print(f"❌ Ошибка в block_user_cmd: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='unblock')
async def unblock_user_cmd(ctx, user_id: str = None):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        if not user_id:
            await ctx.send("❌ Укажите ID пользователя для разблокировки!")
            return
        
        user_to_unblock = int(user_id)
        
        if unblock_user(ctx.author.id, user_to_unblock):
            await ctx.send(f"✅ Пользователь <@{user_id}> разблокирован!", ephemeral=True)
        else:
            await ctx.send("❌ Пользователь не был заблокирован!", ephemeral=True)
            
    except ValueError:
        await ctx.send("❌ Укажите корректный ID пользователя!")
    except Exception as e:
        print(f"❌ Ошибка в unblock_user_cmd: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='blocked')
async def list_blocked(ctx):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        data = load_blocked_users()
        blocked = data["blocked"].get(str(ctx.author.id), [])
        
        if not blocked:
            await ctx.send("📭 У вас нет заблокированных пользователей.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🚫 Заблокированные пользователи",
            description=f"Всего: {len(blocked)}",
            color=discord.Color.red()
        )
        
        blocked_list = []
        for uid in blocked:
            try:
                user = await bot.fetch_user(int(uid))
                blocked_list.append(f"• {user.name} (`{uid}`)")
            except:
                blocked_list.append(f"• Неизвестный пользователь (`{uid}`)")
        
        embed.add_field(name="📋 Список", value="\n".join(blocked_list) if blocked_list else "Нет данных", inline=False)
        
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"❌ Ошибка в list_blocked: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='set_welcome')
async def set_welcome(ctx, style_name: str = None):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ У вас нет прав администратора!")
            return
        
        if not style_name:
            styles = ", ".join(WELCOME_STYLES.keys())
            await ctx.send(f"📋 Доступные стили: {styles}\nИспользуйте `!set_welcome <название_стиля>`")
            return
        
        if set_welcome_style(style_name):
            await ctx.send(f"✅ Стиль приветствия изменен на: **{style_name}**")
            
            welcome_channel = discord.utils.get(ctx.guild.channels, name=WELCOME_CHANNEL_NAME)
            if welcome_channel:
                await create_welcome_message(welcome_channel, ctx.guild)
        else:
            styles = ", ".join(WELCOME_STYLES.keys())
            await ctx.send(f"❌ Стиль '{style_name}' не найден! Доступные: {styles}")
    except Exception as e:
        print(f"❌ Ошибка в set_welcome: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='reset_welcome')
async def reset_welcome(ctx):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ У вас нет прав администратора!")
            return
        
        welcome_channel = discord.utils.get(ctx.guild.channels, name=WELCOME_CHANNEL_NAME)
        if welcome_channel:
            await create_welcome_message(welcome_channel, ctx.guild)
            await ctx.send("✅ Приветственное сообщение пересоздано!")
        else:
            await ctx.send(f"❌ Канал '{WELCOME_CHANNEL_NAME}' не найден!")
    except Exception as e:
        print(f"❌ Ошибка в reset_welcome: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='moderate')
async def moderate_channel(ctx, channel: discord.TextChannel = None):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ У вас нет прав администратора!")
            return
        
        if not channel:
            channel = discord.utils.get(ctx.guild.channels, name=DATING_CHANNEL_NAME)
            if not channel:
                await ctx.send(f"❌ Канал '{DATING_CHANNEL_NAME}' не найден!")
                return
        
        await ctx.send(f"🔍 Начинаю проверку канала {channel.mention}...")
        await moderate_existing_messages(channel)
    except Exception as e:
        print(f"❌ Ошибка в moderate_channel: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='stats')
async def show_stats(ctx):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        data = load_applications_data()
        chat_data = load_active_chats()
        blocked_data = load_blocked_users()
        temp_data = load_temp_channels()
        
        total_applications = len(data["applications"])
        active_chats = sum(1 for chat in chat_data["chats"].values() if chat.get("is_active", False))
        total_chats = len(chat_data["chats"])
        total_blocked = sum(len(blocked) for blocked in blocked_data["blocked"].values())
        active_channels = sum(1 for ch in temp_data["channels"].values() if ch.get("is_active", True))
        
        embed = discord.Embed(
            title="📊 Статистика бота",
            description="Текущая статистика работы бота",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="📝 Всего заявок", value=str(total_applications), inline=True)
        embed.add_field(name="💬 Активных диалогов", value=str(active_chats), inline=True)
        embed.add_field(name="📋 Всего диалогов", value=str(total_chats), inline=True)
        embed.add_field(name="🚫 Всего блокировок", value=str(total_blocked), inline=True)
        embed.add_field(name="🔒 Активных каналов", value=str(active_channels), inline=True)
        embed.add_field(name="🤖 Пользователей", value=str(len(bot.users)), inline=True)
        embed.add_field(name="🔄 Серверов", value=str(len(bot.guilds)), inline=True)
        
        embed.set_footer(text=f"Время работы: {discord.utils.utcnow() - bot.user.created_at}")
        
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"❌ Ошибка в show_stats: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='create_chat')
async def create_chat_cmd(ctx, user_id: str = None):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        if not user_id:
            await ctx.send("❌ Укажите ID пользователя!")
            return
        
        target_user = await bot.fetch_user(int(user_id))
        if not target_user:
            await ctx.send("❌ Пользователь не найден!")
            return
        
        if str(ctx.author.id) == user_id:
            await ctx.send("❌ Вы не можете создать чат с самим собой!")
            return
        
        if is_user_blocked(ctx.author.id, user_id):
            await ctx.send("❌ Вы заблокировали этого пользователя!")
            return
        
        if is_user_blocked(user_id, ctx.author.id):
            await ctx.send("❌ Этот пользователь заблокировал вас!")
            return
        
        application_id = f"manual_{int(datetime.now().timestamp())}"
        
        # Сразу показываем выбор режима
        embed = discord.Embed(
            title="🔒 Выберите режим чата",
            description="Как вы хотите общаться?",
            color=discord.Color.blue()
        )
        
        view = AnonymousStartView(application_id, ctx.author.id, user_id)
        await ctx.send(embed=embed, view=view)
            
    except ValueError:
        await ctx.send("❌ Укажите корректный ID пользователя!")
    except Exception as e:
        print(f"❌ Ошибка в create_chat_cmd: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

@bot.command(name='clean_apps')
async def clean_applications(ctx):
    try:
        if not ctx.guild:
            await ctx.send("❌ Эта команда доступна только на сервере!")
            return
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ У вас нет прав администратора!")
            return
        
        data = load_applications_data()
        deleted_count = 0
        
        for app_id, app_data in list(data["applications"].items()):
            active_chats = ChatManager.get_active_chat_for_application(app_id)
            if not active_chats:
                message_id = app_data.get("message_id")
                if message_id:
                    dating_channel = discord.utils.get(ctx.guild.channels, name=DATING_CHANNEL_NAME)
                    if dating_channel:
                        try:
                            message = await dating_channel.fetch_message(int(message_id))
                            if message:
                                await message.delete()
                        except:
                            pass
                
                del data["applications"][app_id]
                deleted_count += 1
        
        save_applications_data(data)
        await ctx.send(f"✅ Удалено неактивных заявок: {deleted_count}")
    except Exception as e:
        print(f"❌ Ошибка в clean_applications: {e}")
        await ctx.send("❌ Произошла ошибка.", ephemeral=True)

# ==================== ЗАПУСК БОТА ====================

@bot.event
async def on_ready():
    try:
        print(f'✅ Бот запущен как {bot.user}')
        print(f'📊 На серверах: {len(bot.guilds)}')
        print(f'👥 Пользователей: {len(bot.users)}')
        
        for guild in bot.guilds:
            await assign_main_role_for_guild(guild)
            await find_or_create_role(guild, NEWBIE_ROLE_NAME, discord.Color.light_gray())
            
            welcome_channel = discord.utils.get(guild.channels, name=WELCOME_CHANNEL_NAME)
            if not welcome_channel:
                try:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
                    }
                    welcome_channel = await guild.create_text_channel(
                        WELCOME_CHANNEL_NAME,
                        overwrites=overwrites,
                        topic="Канал приветствия и регистрации"
                    )
                    print(f"✅ Создан канал: {welcome_channel.name}")
                except Exception as e:
                    print(f"❌ Ошибка создания канала: {e}")
            
            if welcome_channel:
                await create_welcome_message(welcome_channel, guild)
            
            category_name = "💬 Приватные чаты"
            if not discord.utils.get(guild.categories, name=category_name):
                try:
                    await guild.create_category(category_name)
                    print(f"✅ Создана категория: {category_name}")
                except Exception as e:
                    print(f"❌ Ошибка создания категории: {e}")
            
            # Создаем архивный канал
            archive_channel = discord.utils.get(guild.channels, name=ARCHIVE_CHANNEL_NAME)
            if not archive_channel:
                try:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    }
                    archive_channel = await guild.create_text_channel(
                        ARCHIVE_CHANNEL_NAME,
                        overwrites=overwrites,
                        topic="Архив завершенных чатов"
                    )
                    print(f"✅ Создан архивный канал: {archive_channel.name}")
                except Exception as e:
                    print(f"❌ Ошибка создания архивного канала: {e}")
        
        for guild in bot.guilds:
            dating_channel = discord.utils.get(guild.channels, name=DATING_CHANNEL_NAME)
            if dating_channel:
                await moderate_existing_messages(dating_channel)
        
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Небесные Врата | !help"
            )
        )
    except Exception as e:
        print(f"❌ Ошибка в on_ready: {e}")

@bot.event
async def on_member_join(member):
    try:
        await assign_newbie_role(member)
        print(f"👋 Новый участник: {member.name} на сервере {member.guild.name}")
    except Exception as e:
        print(f"❌ Ошибка в on_member_join: {e}")

@bot.event
async def on_member_remove(member):
    try:
        print(f"👋 Пользователь покинул сервер: {member.name}")
    except Exception as e:
        print(f"❌ Ошибка в on_member_remove: {e}")

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    TOKEN = os.environ.get('DISCORD_TOKEN')
    
    if not TOKEN:
        print("❌ ОШИБКА: Не найден DISCORD_TOKEN в переменных окружения!")
        print("📝 Создайте файл .env и добавьте туда:")
        print("DISCORD_TOKEN=ваш_токен")
        sys.exit(1)
    
    try:
        print("🚀 Запуск бота...")
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        sys.exit(1)