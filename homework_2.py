from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import logging
import asyncio
import time

API_TOKEN = '7839860873:AAG1ZxX5j-hZP4Sdj3l-vBdQdqAt6ZhKt5M'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

users = set()
banned_users = {}
admin_id = 6267512015  

def log_event(event):
    logging.info(event)

button_help = KeyboardButton(text="Помощь")
keyboard = ReplyKeyboardMarkup(
    keyboard=[[button_help]],
    resize_keyboard=True
)

@dp.message(Command('start'))
async def start(message: types.Message):
    users.add(message.from_user.id)
    if message.from_user.id == admin_id:
        log_event(f"Администратор {message.from_user.id} запустил бота.")
        await message.answer(f"Добро пожаловать, {message.from_user.first_name}! Вы вошли как администратор.", reply_markup=keyboard)
    else:
        log_event(f"Пользователь {message.from_user.id} запустил бота.")
        await message.answer(f"Добро пожаловать, {message.from_user.first_name}! Рад видеть вас.", reply_markup=keyboard)

@dp.message(Command('help'))
async def help(message: types.Message):
    if message.from_user.id == admin_id:
        await message.answer("""
        Список команд для администратора:
        /start — Приветствие
        /help — Список команд
        /ban <user_id> <время_в_минутах> — Заблокировать пользователя
        /unban <user_id> — Разблокировать пользователя
        /banned_users — Список заблокированных пользователей
        /broadcast <сообщение> — Рассылка всем пользователям
        """)
    else:
        await message.answer("""
        Список команд для обычных пользователей:
        /start — Приветствие
        /help — Список команд
        """)

@dp.message(Command('ban'))
async def ban(message: types.Message):
    if message.from_user.id == admin_id:
        parts = message.text.split()
        if len(parts) >= 2:
            user_id = int(parts[1])
            confirmation_msg = await message.answer(f"Подтвердите действие для пользователя {user_id}. (Да/Нет)")

            @dp.message(lambda msg: msg.from_user.id == message.from_user.id and msg.text.lower() in ["да", "нет"])
            async def confirm_ban(confirmation: types.Message):
                if confirmation.text.lower() == "да":
                    if len(parts) == 3:
                        duration = int(parts[2])
                        banned_users[user_id] = time.time() + duration * 60
                        log_event(f"Пользователь {user_id} забанен на {duration} минут.")
                        await message.answer(f"Пользователь {user_id} заблокирован на {duration} минут.")
                    else:
                        banned_users[user_id] = time.time() + 60 * 60  
                        log_event(f"Пользователь {user_id} забанен на 1 час.")
                        await message.answer(f"Пользователь {user_id} заблокирован на 1 час.")
                elif confirmation.text.lower() == "нет":
                    await message.answer(f"Действие для пользователя {user_id} отменено.")
                else:
                    await message.answer("Пожалуйста, ответьте 'Да' или 'Нет'.")
                await confirmation_msg.delete()
        else:
            await message.answer("Необходимо указать user_id и время (в минутах).")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('unban'))
async def unban(message: types.Message):
    if message.from_user.id == admin_id:
        parts = message.text.split()
        if len(parts) == 2:
            user_id = int(parts[1])
            if user_id in banned_users:
                del banned_users[user_id]
                log_event(f"Пользователь {user_id} был разблокирован.")
                await message.answer(f"Пользователь {user_id} был разблокирован.")
            else:
                await message.answer(f"Пользователь {user_id} не заблокирован.")
        else:
            await message.answer("Необходимо указать user_id.")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('banned_users'))
async def banned_users_list(message: types.Message):
    if message.from_user.id == admin_id:
        if banned_users:
            banned_list = "\n".join([str(user_id) for user_id in banned_users])
            await message.answer(f"Заблокированные пользователи:\n{banned_list}")
        else:
            await message.answer("Нет заблокированных пользователей.")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message(Command('broadcast'))
async def broadcast(message: types.Message):
    if message.from_user.id == admin_id:
        parts = message.text.split(" ", 1)
        if len(parts) == 2:
            message_to_send = parts[1]
            for user_id in users:
                try:
                    await bot.send_message(user_id, message_to_send)
                    log_event(f"Рассылка: Сообщение отправлено пользователю {user_id}.")
                except:
                    log_event(f"Ошибка при отправке сообщения пользователю {user_id}.")
            await message.answer(f"Сообщение было отправлено всем пользователям.")
        else:
            await message.answer("Необходимо указать текст сообщения.")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@dp.message()
async def echo(message: types.Message):
    if message.from_user.id in banned_users and banned_users[message.from_user.id] > time.time():
        await message.answer("Вы заблокированы! Пожалуйста, подождите.")
        return
    if not message.text.startswith("/"):
        await message.answer(f"Вы написали: {message.text}")

async def on_start():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(on_start())