import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.enums import ContentType
import aiosqlite

logging.basicConfig(level=logging.INFO)

API_TOKEN = '7839860873:AAG1ZxX5j-hZP4Sdj3l-vBdQdqAt6ZhKt5M'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class Form(StatesGroup):
    photo = State()
    caption = State()
    confirm = State()

async def init_db():
    async with aiosqlite.connect('media.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                caption TEXT
            )
        ''')
        await db.commit()

async def add_media(file_id: str, caption: str):
    async with aiosqlite.connect('media.db') as db:
        await db.execute('INSERT INTO media (file_id, caption) VALUES (?, ?)', (file_id, caption))
        await db.commit()

async def get_all_media():
    async with aiosqlite.connect('media.db') as db:
        async with db.execute('SELECT * FROM media') as cursor:
            return await cursor.fetchall()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Привет! Отправь мне фотографию.")
    await state.set_state(Form.photo)

@dp.message(Form.photo, lambda message: message.content_type == ContentType.PHOTO)
async def process_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(file_id=file_id)
    await message.answer("Теперь введи подпись к фото.")
    await state.set_state(Form.caption)

@dp.message(Form.photo)
async def process_photo_invalid(message: types.Message):
    await message.answer("Пожалуйста, отправь фотографию.")

@dp.message(Form.caption)
async def process_caption(message: types.Message, state: FSMContext):
    caption = message.text
    await state.update_data(caption=caption)
    data = await state.get_data()
    await message.answer_photo(data['file_id'], caption=f"Подпись: {caption}")
    await message.answer("Сохранить это? (Да/Нет)")
    await state.set_state(Form.confirm)

@dp.message(Form.confirm)
async def process_confirm(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        data = await state.get_data()
        await add_media(data['file_id'], data['caption'])
        await message.answer("Данные сохранены.")
    else:
        await message.answer("Данные не сохранены.")
    await state.clear()

@dp.message(Command("showall"))
async def cmd_showall(message: types.Message):
    media_list = await get_all_media()
    if media_list:
        for media in media_list:
            await message.answer_photo(media[1], caption=f"ID: {media[0]}\nПодпись: {media[2]}")
    else:
        await message.answer("В базе данных пока нет записей.")

async def on_startup():
    await init_db()

if __name__ == '__main__':
    import asyncio
    asyncio.run(on_startup())
    dp.run_polling(bot)