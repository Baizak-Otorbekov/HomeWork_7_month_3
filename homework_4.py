import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiosqlite

logging.basicConfig(level=logging.INFO)

API_TOKEN = '7839860873:AAG1ZxX5j-hZP4Sdj3l-vBdQdqAt6ZhKt5M'
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class AddItemStates(StatesGroup):
    name = State()
    price = State()

async def init_db():
    async with aiosqlite.connect('shop.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        await db.commit()

async def add_item(name: str, price: float):
    async with aiosqlite.connect('shop.db') as db:
        await db.execute('INSERT INTO items (name, price) VALUES (?, ?)', (name, price))
        await db.commit()

async def get_all_items():
    async with aiosqlite.connect('shop.db') as db:
        async with db.execute('SELECT * FROM items') as cursor:
            return await cursor.fetchall()

async def delete_item(item_id: int):
    async with aiosqlite.connect('shop.db') as db:
        await db.execute('DELETE FROM items WHERE id = ?', (item_id,))
        await db.commit()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Добро пожаловать! Используйте команды /add_item, /list_items, /delete_item.")

@dp.message(Command("add_item"))
async def cmd_add_item(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара:")
    await state.set_state(AddItemStates.name)

@dp.message(AddItemStates.name)
async def process_item_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите цену товара (только число):")
    await state.set_state(AddItemStates.price)

@dp.message(AddItemStates.price)
async def process_item_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        data = await state.get_data()
        await add_item(data['name'], price)
        await message.answer(f"Товар '{data['name']}' с ценой {price} успешно добавлен!")
        await state.clear()
    except ValueError:
        await message.answer("Цена должна быть числом. Попробуйте снова.")

@dp.message(Command("list_items"))
async def cmd_list_items(message: types.Message):
    items = await get_all_items()
    if items:
        response = "Список товаров:\n"
        for item in items:
            response += f"{item[0]}. {item[1]} - {item[2]} руб.\n"
        await message.answer(response)
    else:
        await message.answer("Товаров пока нет.")

@dp.message(Command("delete_item"))
async def cmd_delete_item(message: types.Message):
    items = await get_all_items()
    if items:
        keyboard = InlineKeyboardBuilder()
        for item in items:
            keyboard.add(InlineKeyboardButton(text=f"{item[1]} - {item[2]} руб.", callback_data=f"delete_{item[0]}"))
        await message.answer("Выберите товар для удаления:", reply_markup=keyboard.as_markup())
    else:
        await message.answer("Товаров пока нет.")

@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def process_delete_item(callback: types.CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    await delete_item(item_id)
    await callback.answer(f"Товар удален!")
    await callback.message.answer("Товар успешно удален.")

async def on_startup():
    await init_db()

if __name__ == '__main__':
    import asyncio
    asyncio.run(on_startup())
    dp.run_polling(bot)