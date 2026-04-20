import os
import sqlite3
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "Alimzhan")
ADMIN_PASS = os.getenv("ADMIN_PASS", "747005")
DB_PATH = os.getenv("DB_PATH", "virus_edu.db")

if not BOT_TOKEN:
    raise ValueError("❌ ОШИБКА: Переменная BOT_TOKEN не найдена в окружении!")

# ================= ЛОГИРОВАНИЕ =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ================= БАЗА ДАННЫХ =================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS viruses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT,
            description TEXT,
            danger TEXT,
            symptoms TEXT,
            protection TEXT
        )
    """)
    count = cursor.execute("SELECT COUNT(*) FROM viruses").fetchone()[0]
    if count == 0:
        data = [
            ('Троян', 'Malware', 'Проникает под видом полезной программы', '🔴 Высокая', 'Кража паролей', 'Не запускать .exe'),
            ('Червь', 'Network Virus', 'Копируется по сети', '🟡 Средняя', 'Тормозит интернет', 'Обновлять ОС'),
            ('Шпион', 'Spyware', 'Скрытно следит за действиями', '🔴 Высокая', 'Реклама, лаги', 'Антишпион'),
            ('Рансомвер', 'Ransomware', 'Шифрует файлы и требует выкуп', '🔴 Критическая', 'Файлы не открываются', 'Бэкапы'),
            ('SQL Injection', 'Web Attack', 'Взлом через поля ввода', '🔴 Высокая', 'Утечка данных', 'Параметризованные запросы')
        ]
        cursor.executemany("INSERT OR IGNORE INTO viruses VALUES (NULL,?,?,?,?,?,?)", data)
        conn.commit()
        logger.info("✅ База данных инициализирована и заполнена")
    conn.close()

# ================= FSM СОСТОЯНИЯ =================
class AdminLoginState(StatesGroup):
    login = State()
    password = State()

class AddVirusState(StatesGroup):
    name = State()
    v_type = State()
    desc = State()
    danger = State()
    symp = State()
    prot = State()
    confirm = State()

# Хранилище сессий админов
admin_sessions = {}

# ================= ИНИЦИАЛИЗАЦИЯ БОТА =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Клавиатуры
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🦠 Все вирусы"), KeyboardButton(text="🔍 Поиск")],
    [KeyboardButton(text="🛡️ Защита"), KeyboardButton(text="🧠 Тест")],
], resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ Добавить вирус"), KeyboardButton(text="📋 Список")],
    [KeyboardButton(text="🔙 В главное меню")],
], resize_keyboard=True)

# ================= КОМАНДЫ =================
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    if msg.from_user.id in admin_sessions:
        del admin_sessions[msg.from_user.id]
    await msg.answer("👋 Привет! Я VirusEduBot.\n\nВыбери действие:", reply_markup=main_kb)

@dp.message(Command("help"))
async def cmd_help(msg: types.Message):
    await msg.answer("📖 Команды:\n/start - Главное меню\n/admin - Вход для админа\n/help - Помощь")

# 🔐 ВХОД В АДМИНКУ
@dp.message(Command("admin"))
async def cmd_admin(msg: types.Message, state: FSMContext):
    logger.info(f"🔐 Попытка входа в админку: {msg.from_user.id}")
    await msg.answer("🔐 Вход в админ-панель.\n\nВведи логин:")
    await state.set_state(AdminLoginState.login)

# ================= ЛОГИН И ПАРОЛЬ =================
@dp.message(AdminLoginState.login)
async def process_login(msg: types.Message, state: FSMContext):
    if msg.text.strip() != ADMIN_LOGIN:
        await state.clear()
        return await msg.answer("❌ Неверный логин. Попробуй /admin")
    await state.update_data(login=msg.text)
    await state.set_state(AdminLoginState.password)
    await msg.answer("🔑 Введи пароль:")

@dp.message(AdminLoginState.password)
async def process_password(msg: types.Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        await state.clear()
        return await msg.answer("🚫 Доступ запрещён (твой ID не в списке)")
    if msg.text.strip() != ADMIN_PASS:
        await state.clear()
        return await msg.answer("❌ Неверный пароль.")

    admin_sessions[msg.from_user.id] = True
    await state.clear()
    logger.info(f"✅ Админ {msg.from_user.id} успешно вошёл")
    await msg.answer("✅ Добро пожаловать в админ-панель!", reply_markup=admin_kb)

# ================= АДМИН ПАНЕЛЬ =================
@dp.message(F.text == "➕ Добавить вирус")
async def add_virus_start(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in admin_sessions:
        return await msg.answer("🔒 Сначала войди как админ: /admin")
    await state.set_state(AddVirusState.name)
    await msg.answer("1️⃣ Введи название вируса:")

@dp.message(AddVirusState.name)
async def add_virus_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(AddVirusState.v_type)
    await msg.answer("2️⃣ Введи тип:")

@dp.message(AddVirusState.v_type)
async def add_virus_type(msg: types.Message, state: FSMContext):
    await state.update_data(v_type=msg.text)
    await state.set_state(AddVirusState.desc)
    await msg.answer("3️⃣ Введи описание:")

@dp.message(AddVirusState.desc)
async def add_virus_desc(msg: types.Message, state: FSMContext):
    await state.update_data(desc=msg.text)
    await state.set_state(AddVirusState.danger)
    await msg.answer("4️⃣ Введи уровень опасности (🔴/🟡):")

@dp.message(AddVirusState.danger)
async def add_virus_danger(msg: types.Message, state: FSMContext):
    await state.update_data(danger=msg.text)
    await state.set_state(AddVirusState.symp)
    await msg.answer("5️⃣ Введи симптомы:")

@dp.message(AddVirusState.symp)
async def add_virus_symp(msg: types.Message, state: FSMContext):
    await state.update_data(symp=msg.text)
    await state.set_state(AddVirusState.prot)
    await msg.answer("6️⃣ Введи защиту:")

@dp.message(AddVirusState.prot)
async def add_virus_prot(msg: types.Message, state: FSMContext):
    await state.update_data(prot=msg.text)
    await state.set_state(AddVirusState.confirm)
    data = await state.get_data()
    await msg.answer(f"✅ Сохранить вирус?\n\n🦠 {data['name']}\n📂 {data['v_type']}\n⚠️ {data['danger']}\n\nНапиши ДА или НЕТ")

@dp.message(AddVirusState.confirm)
async def add_virus_confirm(msg: types.Message, state: FSMContext):
    if msg.text.lower() != "да":
        await state.clear()
        return await msg.answer("❌ Отменено.")
    data = await state.get_data()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO viruses VALUES (NULL,?,?,?,?,?,?)",
            (data['name'], data['v_type'], data['desc'], data['danger'], data['symp'], data['prot']))
        conn.commit()
        logger.info(f"✅ Добавлен вирус: {data['name']}")
        await msg.answer("✅ Вирус успешно добавлен!")
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")
        await msg.answer(f"❌ Ошибка: {e}")
    finally:
        conn.close()
    await state.clear()

@dp.message(F.text == "📋 Список")
async def show_list(msg: types.Message):
    if msg.from_user.id not in admin_sessions:
        return await msg.answer("🔒 Доступно только для админа")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, name, danger FROM viruses").fetchall()
    conn.close()
    text = "📋 Список вирусов:\n" + "\n".join([f"{r[0]}. {r[1]} {r[2]}" for r in rows])
    await msg.answer(text)

# ================= ПОЛЬЗОВАТЕЛЬСКИЕ ФУНКЦИИ =================
@dp.message(F.text == "🦠 Все вирусы")
async def show_all(msg: types.Message):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, name, danger FROM viruses").fetchall()
    conn.close()
    text = "🦠 Все вирусы в базе:\n" + "\n".join([f"{r[0]}. {r[1]} {r[2]}" for r in rows])
    await msg.answer(text)

@dp.message(F.text == "🔍 Поиск")
async def search_prompt(msg: types.Message):
    await msg.answer("🔎 Напиши название вируса для поиска:")

@dp.message(F.text == "🛡️ Защита")
async def protect(msg: types.Message):
    await msg.answer("🛡️ Правила безопасности:\n1. Установи антивирус\n2. Обновляй систему\n3. Делай бэкапы\n4. Используй 2FA\n5. Не открывай подозрительные ссылки")

@dp.message(F.text == "🧠 Тест")
async def quiz(msg: types.Message):
    await msg.answer("🧠 Вопрос: Какой вирус шифрует файлы?\n\n1) Червь\n2) Рансомвер\n\nНапиши 1 или 2")

@dp.message(F.text == "🔙 В главное меню")
async def back_menu(msg: types.Message):
    if msg.from_user.id in admin_sessions:
        del admin_sessions[msg.from_user.id]
    await cmd_start(msg)

# ================= ОБЩИЙ ОБРАБОТЧИК ТЕКСТА =================
@dp.message(F.text)
async def handle_text(msg: types.Message):
    # Ответ на тест
    if msg.text.strip() == "2":
        return await msg.answer("✅ Правильно! Рансомвер шифрует файлы.")
    elif msg.text.strip() == "1":
        return await msg.answer("❌ Неверно. Правильный ответ: 2")

    # Поиск вируса
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT name FROM viruses WHERE name LIKE ?", (f"%{msg.text.strip()}%",)).fetchall()
    conn.close()

    if rows:
        await msg.answer("🔍 Найдено: " + ", ".join([r[0] for r in rows]))
    else:
        await msg.answer("❌ Не найдено. Попробуй: Троян, Trojan, SQL")

# ================= ЗАПУСК =================
async def main():
    init_db()
    logger.info("✅ Бот успешно запущен!")
    print("=" * 40)
    print(f"🔐 Админ: {ADMIN_LOGIN} / {ADMIN_PASS}")
    print(f"👤 Твой ID: {ADMIN_ID}")
    print("=" * 40)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
