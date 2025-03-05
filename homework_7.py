import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import BaseFilter, Command
from aiogram.dispatcher.middlewares.base import BaseMiddleware

TOKEN = '7839860873:AAG1ZxX5j-hZP4Sdj3l-vBdQdqAt6ZhKt5M'

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

class LoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: dict):
        user_id = event.from_user.id
        text = event.text

        logging.info(f"User ID: {user_id}, Message: {text}")

        if text.lower() == "привет":
            await event.answer("Привет! Как дела?")
            return

        return await handler(event, data)

class BotFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return any(word in message.text.lower() for word in ["бот", "ботик", "bot"])

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.message.middleware(LoggerMiddleware())

    @dp.message(Command("start"))
    async def start_handler(message: types.Message):
        await message.answer("Привет! Я бот.")

    @dp.message(BotFilter())
    async def bot_response(message: types.Message):
        await message.answer("Да, я бот! Чем помочь?")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())