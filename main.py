import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from dotenv import load_dotenv

# Загружаем настройки из файла .env
load_dotenv()

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_STR = os.getenv("ADMIN_ID", "0")
ADMIN_ID = int(ADMIN_ID_STR) if ADMIN_ID_STR.isdigit() else 0
DB_PATH = os.getenv("DB_PATH", "virus_edu.db")

if not BOT_TOKEN:
    raise ValueError("❌ ОШИБКА: Не указан BOT_TOKEN в файле .env!")


# ================= 1. БАЗА ДАННЫХ =================
def init_db():
    print("🔄 Инициализация базы данных...")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Создаём таблицу
        c.execute("""CREATE TABLE IF NOT EXISTS viruses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, type TEXT,
            description TEXT, danger TEXT, symptoms TEXT, protection TEXT
        )""")
        conn.commit()

        # Проверяем количество записей
        count = c.execute("SELECT COUNT(*) FROM viruses").fetchone()[0]

        if count == 0:
            print("📦 База пуста. Заполняю данными...")
            data = [
                # Русские вирусы
                ('Троян', 'Вредоносное ПО', 'Проникает под видом полезной программы, создает черный ход для хакера.',
                 '🔴 Высокая', 'Кража паролей, самопроизвольные действия, установка вирусов.',
                 'Не запускать .exe из непроверенных источников, проверять цифровые подписи.'),
                ('Червь', 'Сетевой вирус', 'Сам копируется по сети, используя уязвимости операционной системы.',
                 '🟡 Средняя', 'Тормозит интернет, рассылает спам, высокая нагрузка на CPU.',
                 'Обновлять Windows, использовать фаервол, закрывать порты.'),
                ('Шпион', 'Spyware', 'Скрытно следит за экраном, камерой, микрофоном и действиями пользователя.',
                 '🔴 Высокая', 'Всплывающая реклама, разряд батареи, изменение настроек браузера.',
                 'Запрещать доступ к камере неизвестным приложениям, антишпионские утилиты.'),
                ('Рансомвер', 'Шифровальщик', 'Шифрует все файлы пользователя и требует выкуп за расшифровку.',
                 '🔴 Критическая', 'Файлы не открываются, требование денег на экране, расширения .locked.',
                 'Делать бэкапы на внешний диск (правило 3-2-1), не платить выкуп.'),
                ('Руткит', 'Stealth Malware',
                 'Прячется глубоко в ядре системы, невидим для антивируса и диспетчера задач.', '🔴 Критическая',
                 'Антивирус не запускается, исчезают системные утилиты, странные процессы.',
                 'Переустановка ОС, проверка с загрузочного диска LiveCD.'),
                ('Кейлоггер', 'Keylogger', 'Записывает все нажатия клавиш для кражи паролей и переписки.', '🔴 Высокая',
                 'Задержки при печати текста, неизвестные процессы в фоне.',
                 'Использовать виртуальную клавиатуру, двухфакторная аутентификация 2FA.'),
                ('Макровирус', 'Document Virus', 'Живет внутри документов Word и Excel через макросы (скрипты).',
                 '🟡 Средняя', 'Просит включить макросы при открытии, странное форматирование.',
                 'Отключить макросы в настройках Office, не открывать .docm из почты.'),
                ('Логическая бомба', 'Logic Bomb', 'Спит до определенной даты или действия, затем наносит вред.',
                 '🟡 Средняя', 'Работает нормально месяцами, потом вдруг удаляет данные.',
                 'Аудит кода, контроль изменений в системных файлах, мониторинг.'),
                ('Файловый вирус', 'File Infector', 'Прилипает к программам (.exe, .dll), активируется при их запуске.',
                 '🟡 Средняя', 'Программы весят больше, долго грузятся, ошибки памяти.',
                 'Проверять хеш-суммы файлов, хранить оригинальные установщики.'),
                ('Ботнет', 'Botnet Agent', 'Превращает ПК в зомби для атак на сайты или майнинга криптовалюты.',
                 '🔴 Высокая', 'Высокий трафик в простое, сильные тормоза, неизвестные соединения.',
                 'Закрыть порты роутера, следить за сетевой активностью в диспетчере.'),

                # Английские вирусы
                ('Trojan', 'Malware', 'Disguises as legitimate software to create backdoors for hackers.', '🔴 High',
                 'Password theft, unexpected actions, installation of malware.',
                 'Do not run untrusted executables, verify digital signatures.'),
                ('Worm', 'Network Virus', 'Self-replicates across networks via OS vulnerabilities.', '🟡 Medium',
                 'Network lag, spam distribution, high CPU usage.', 'Update OS, use firewall, close unused ports.'),
                ('Spyware', 'Surveillance', 'Secretly records screen, camera, microphone and user activity.', '🔴 High',
                 'Pop-up ads, battery drain, browser redirects.', 'Restrict app permissions, use anti-spyware tools.'),
                ('Ransomware', 'Encryptor', 'Encrypts all user files and demands crypto payment for decryption.',
                 '🔴 Critical', 'Files locked, ransom note on desktop, .locked extensions.',
                 'Regular offline backups (3-2-1 rule), do not pay ransom.'),
                ('Rootkit', 'Stealth', 'Hides deep in OS kernel, invisible to antivirus and task manager.',
                 '🔴 Critical', 'Antivirus fails to start, system utilities disappear.',
                 'Reinstall OS or use bootable LiveCD for scanning.'),
                ('Keylogger', 'Recorder', 'Records all keystrokes to steal passwords and messages.', '🔴 High',
                 'Typing lag, unknown background processes.',
                 'Use virtual keyboard, enable Two-Factor Authentication (2FA).'),
                ('Macro Virus', 'Doc Malware', 'Embeds malicious scripts in Word and Excel documents.', '🟡 Medium',
                 'Prompts to enable macros, strange document formatting.',
                 'Disable macros by default in Office settings.'),
                ('Logic Bomb', 'Triggered', 'Dormant until specific date or action triggers malicious payload.',
                 '🟡 Medium', 'Works normally for months, then suddenly deletes data.',
                 'Code audits, monitor system file changes.'),
                ('File Infector', 'Parasitic', 'Attaches to executable files (.exe), activates when program runs.',
                 '🟡 Medium', 'Increased file size, slow launch, memory errors.',
                 'Verify file hashes, keep original installers.'),
                ('Botnet', 'Zombie', 'Turns PC into zombie for DDoS attacks or crypto mining.', '🔴 High',
                 'High outgoing traffic when idle, system lag.', 'Close router ports, monitor network activity.'),

                # Дополнительные
                ('SQL Injection', 'Web Attack',
                 'Exploits vulnerable web forms to manipulate database queries and steal data.', '🔴 High',
                 'Data leakage, unauthorized admin access, database errors.',
                 'Use parameterized queries, input validation, Web Application Firewall.'),
                ('SQL-инъекция', 'Веб-атака',
                 'Взлом сайта через поля ввода для управления базой данных и кражи информации.', '🔴 Высокая',
                 'Утечка данных, несанкционированный доступ к админке.',
                 'Параметризованные запросы, фильтрация ввода, WAF.')
            ]
            c.executemany("INSERT OR IGNORE INTO viruses VALUES (NULL,?,?,?,?,?,?)", data)
            conn.commit()
            print(f"✅ База успешно заполнена! Добавлено {len(data)} вирусов.")
        else:
            print(f"✅ База уже содержит {count} записей.")
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")


# ================= 2. FSM (Админка) =================
class AddVirusState(StatesGroup):
    name = State()
    v_type = State()
    desc = State()
    danger = State()
    symp = State()
    prot = State()
    confirm = State()


# ================= 3. БОТ =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🦠 Все вирусы"), KeyboardButton(text="🔍 Поиск")],
    [KeyboardButton(text="🛡️ Защита ПК"), KeyboardButton(text="🧠 Тест")],
    [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="➕ Добавить (Админ)")]
], resize_keyboard=True)


# --- Команды ---
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await msg.answer(
        "👋 Привет! Я «ВирусЭду» — энциклопедия кибербезопасности.\n\n"
        "📚 Узнай о вирусах (на русском и английском)\n"
        "🛡️ Как защититься от угроз\n"
        "🧠 Проверь свои знания\n\n"
        "Выбери действие в меню 👇",
        reply_markup=main_kb
    )


@dp.message(Command("myid"))
async def cmd_myid(msg: types.Message):
    await msg.answer(
        f"🆔 Твой Telegram ID:\n"
        f"<code>{msg.from_user.id}</code>\n\n"
        f"Скопируй это число в файл .env в строку ADMIN_ID",
        parse_mode="HTML"
    )


@dp.message(Command("help"))
async def cmd_help(msg: types.Message):
    await msg.answer(
        "📖 Команды:\n"
        "/start - Главное меню\n"
        "/myid - Узнать свой ID\n"
        "/add_new - Добавить вирус (админ)\n"
        "/cancel - Отменить действие"
    )


@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Действие отменено.")


@dp.message(Command("add_new"))
async def start_add(msg: types.Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer(
            "🔒 Доступ запрещен. Вы не админ.\n\n"
            f"Твой ID: {msg.from_user.id}\n"
            "Напиши /myid и добавь свой ID в файл .env"
        )
    await msg.answer(
        "🆕 **Добавление вируса**\n"
        "Отправь /cancel для отмены.",
        parse_mode="Markdown"
    )
    await state.set_state(AddVirusState.name)
    await msg.answer("1️⃣ Введи название вируса:")


# --- Шаги добавления ---
@dp.message(AddVirusState.name)
async def get_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(AddVirusState.v_type)
    await msg.answer("2️⃣ Введи тип (например: Trojan, Malware):")


@dp.message(AddVirusState.v_type)
async def get_type(msg: types.Message, state: FSMContext):
    await state.update_data(v_type=msg.text)
    await state.set_state(AddVirusState.desc)
    await msg.answer("3️⃣ Введи описание (как работает):")


@dp.message(AddVirusState.desc)
async def get_desc(msg: types.Message, state: FSMContext):
    await state.update_data(desc=msg.text)
    await state.set_state(AddVirusState.danger)
    await msg.answer("4️⃣ Уровень опасности (🟢🟡):")


@dp.message(AddVirusState.danger)
async def get_danger(msg: types.Message, state: FSMContext):
    await state.update_data(danger=msg.text)
    await state.set_state(AddVirusState.symp)
    await msg.answer("5️⃣ Симптомы заражения:")


@dp.message(AddVirusState.symp)
async def get_symp(msg: types.Message, state: FSMContext):
    await state.update_data(symp=msg.text)
    await state.set_state(AddVirusState.prot)
    await msg.answer("6️⃣ Как защититься?")


@dp.message(AddVirusState.prot)
async def get_prot(msg: types.Message, state: FSMContext):
    await state.update_data(prot=msg.text)
    data = await state.get_data()
    summary = (
        f"✅ **Проверь данные:**\n\n"
        f"🦠 Название: {data['name']}\n"
        f"📂 Тип: {data['v_type']}\n"
        f"📝 Описание: {data['desc']}\n"
        f"⚠️ Опасность: {data['danger']}\n"
        f"🚨 Симптомы: {data['symp']}\n"
        f"🛡️ Защита: {data['prot']}\n\n"
        f"Напиши **ДА** чтобы сохранить, или **НЕТ** чтобы отменить."
    )
    await state.set_state(AddVirusState.confirm)
    await msg.answer(summary, parse_mode="Markdown")


@dp.message(AddVirusState.confirm)
async def finish_add(msg: types.Message, state: FSMContext):
    if msg.text.lower() != "да":
        await state.clear()
        return await msg.answer("❌ Сохранение отменено.")

    data = await state.get_data()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO viruses (name, type, description, danger, symptoms, protection) VALUES (?,?,?,?,?,?)",
            (data['name'], data['v_type'], data['desc'], data['danger'], data['symp'], data['prot'])
        )
        conn.commit()
        await msg.answer(f"✅ Вирус \"{data['name']}\" успешно добавлен! 🎉")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")
    finally:
        conn.close()
    await state.clear()


# --- Кнопки меню ---
@dp.message(F.text == "🦠 Все вирусы")
async def show_all(msg: types.Message):
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT id, name, danger FROM viruses").fetchall()
        conn.close()

        if not rows:
            return await msg.answer("📭 База данных пуста.")

        text = "🦠 **Все вирусы в базе:**\n\n"
        kb = InlineKeyboardMarkup(inline_keyboard=[])

        for row in rows:
            text += f"• {row[1]} ({row[2]})\n"
            kb.inline_keyboard.append([
                InlineKeyboardButton(text=f" {row[1]}", callback_data=f"view_{row[0]}")
            ])

        await msg.answer(text, reply_markup=kb, parse_mode="Markdown")
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")


@dp.message(F.text == "🔍 Поиск")
async def search_start(msg: types.Message):
    await msg.answer("🔎 Напиши название вируса (на русском или английском):\n\nПример: Trojan, Троян, SQL")


@dp.message(F.text == "🛡️ Защита ПК")
async def protect_info(msg: types.Message):
    await msg.answer(
        "🛡️ **Основные правила защиты:**\n\n"
        "1️⃣ Установи надёжный антивирус и обновляй его\n"
        "2️⃣ Регулярно обновляй операционную систему\n"
        "3️⃣ Не открывай подозрительные ссылки и вложения\n"
        "4️⃣ Делай резервные копии важных файлов (бэкапы)\n"
        "5️⃣ Используй сложные пароли и 2FA\n"
        "6️⃣ Не скачивай программы с непроверенных сайтов\n\n"
        "💡 Профилактика дешевле лечения!"
    )


@dp.message(F.text == "🧠 Тест")
async def quiz_start(msg: types.Message):
    await msg.answer(
        "🧠 **Вопрос 1:** Какой вирус шифрует файлы и требует выкуп?\n\n"
        "1) Червь (Worm)\n"
        "2) Рансомвер (Ransomware)\n"
        "3) Шпион (Spyware)\n\n"
        "Напиши цифру ответа (1, 2 или 3)."
    )


@dp.message(F.text == "🆘 Помощь")
async def help_info(msg: types.Message):
    await msg.answer(
        "🆘 **Если компьютер заражён:**\n\n"
        "1️⃣ Немедленно отключи интернет (выдерни кабель/выключи Wi-Fi)\n"
        "2️⃣ Загрузись в Безопасном режиме (Safe Mode)\n"
        "3️⃣ Запусти полную проверку антивирусом\n"
        "4️⃣ НЕ плати хакерам выкуп (нет гарантии возврата)\n"
        "5️⃣ Восстанови файлы из резервной копии\n"
        "6️⃣ Смени все пароли с другого устройства\n"
        "7️⃣ При серьёзной угрозе — переустанови ОС\n\n"
        "📞 Обратись к специалисту, если не уверен!"
    )


@dp.message(F.text == "➕ Добавить (Админ)")
async def admin_btn(msg: types.Message, state: FSMContext):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer(
            "🔒 Только для админа!\n\n"
            f"Твой ID: {msg.from_user.id}\n"
            "Напиши /myid и добавь ID в .env"
        )
    await start_add(msg, state)


# --- Обработка текста (Поиск + Тест) ---
@dp.message(F.text)
async def handle_text(msg: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        return  # Если активен FSM, пусть он обрабатывает

    text = msg.text.strip()

    # Ответ на тест
    if text == "2":
        return await msg.answer(
            "✅ **Правильно!** 🎉\n\n"
            "Рансомвер (Ransomware) шифрует файлы и требует выкуп.\n\n"
            "Хочешь ещё вопрос? Нажми 🧠 Тест"
        )
    elif text in ["1", "3"]:
        return await msg.answer(
            "❌ **Неверно.**\n\n"
            "Правильный ответ: **2) Рансомвер**\n\n"
            "Попробуй ещё раз! Нажми 🧠 Тест"
        )

    # Поиск в базе
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT id, name FROM viruses WHERE name LIKE ?",
            (f"%{text}%",)
        ).fetchall()
        conn.close()

        if rows:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=r[1], callback_data=f"view_{r[0]}")] for r in rows
            ])
            await msg.answer(
                f"🔍 **Найдено:** {len(rows)}\n\n"
                f"По запросу \"{text}\":",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        else:
            await msg.answer(
                f"🤷‍️ Ничего не найдено по запросу \"{text}\".\n\n"
                "Попробуй:\n"
                "• Trojan или Троян\n"
                "• SQL Injection\n"
                "• Ransomware"
            )
    except sqlite3.OperationalError:
        await msg.answer(
            "⚠️ База данных ещё не готова.\n"
            "Подожди 5 секунд или напиши /start"
        )
    except Exception as e:
        await msg.answer(f"❌ Ошибка поиска: {e}")


# --- Callback (нажатие на кнопки "Подробнее") ---
@dp.callback_query(F.data.startswith("view_"))
async def view_virus(cb: types.CallbackQuery):
    try:
        vid = cb.data.split("_")[1]
        conn = sqlite3.connect(DB_PATH)
        v = conn.execute("SELECT * FROM viruses WHERE id=?", (vid,)).fetchone()
        conn.close()

        if v:
            info = (
                f"🦠 **{v[1]}**\n\n"
                f"📂 **Тип:** {v[2]}\n"
                f"⚠️ **Опасность:** {v[3]}\n\n"
                f"📝 **Как работает:**\n{v[4]}\n\n"
                f"🚨 **Симптомы:**\n{v[5]}\n\n"
                f"🛡️ **Защита:**\n{v[6]}"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="back_to_list")]
            ])
            await cb.message.edit_text(info, reply_markup=kb, parse_mode="Markdown")
        await cb.answer()
    except Exception as e:
        await cb.answer(f"❌ Ошибка: {e}", show_alert=True)


@dp.callback_query(F.data == "back_to_list")
async def back_to_list(cb: types.CallbackQuery):
    await show_all(cb.message)


# ================= ЗАПУСК =================
async def main():
    print("=" * 50)
    print("🦠 ЗАПУСК БОТА «ВИРУСЭДУ»")
    print("=" * 50)

    # Инициализация БД
    init_db()

    print("\n✅ Бот готов к работе!")
    print("📱 Напиши боту в Telegram: /start")
    print("=" * 50)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен пользователем.")